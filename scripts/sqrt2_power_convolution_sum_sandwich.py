"""AP041: a rectangular product lies between two actual convolution sums.

For L<=M, retain the same input codes and construct the convolution of their
length-M prefixes through length 2*L. Its length-L sum is at most the product
of the input length-L sums, which is at most its length-2*L sum. No analytic
identity or quantitative error is assumed, and L=0 is included.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_convolution_prefix_order import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,convolution_prefix_order_source_pins,
    NAMED_SOURCE as ORDER_SOURCE,HELPER_SOURCES as ORDER_HELPERS,CONVOLUTION_ARCHIVE,
)
from sqrt2_power_convolution_total import NAMED_SOURCE as TOTAL_SOURCE,definition_registry as source_registry
from sqrt2_power_horner_product import TOTAL_ARCHIVE
from sqrt2_power_power_width_transport import LOCAL_ARCHIVE
from sqrt2_power_convolution_locality import HELPER_SOURCES as LOCAL_HELPERS
from sqrt2_power_exp_convolution_recurrence import HELPER_SOURCES as EXP_HELPERS,exp_convolution_recurrence_source_pins
from sqrt2_power_natural_convolution import HELPER_SOURCES as CONVOLUTION_HELPERS
from sqrt2_power_convolution_commutative import SPLIT_ARCHIVE
from sqrt2_power_sum_splitting import NAMED_SOURCE as SPLIT_SOURCE
from sqrt2_power_euler_product import coefficient
from sqrt2_power_exp_two_sided_continuity import _left,_right
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_log_exp_witness import conjoin
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-convolution-sum-sandwich-v1'
A,B,C,D=('ab','ac','L'),('bb','bc','L'),('ab','ac','M'),('bb','bc','M')
P=('ab','ac','bb','bc','L','M')
LONG_PREFIX='NatConvolutionPrefix(ab,ac,M,bb,bc,M,cb,cc,L+L)'
SHORT_PREFIX='NatConvolutionPrefix(ab,ac,L,bb,bc,L,db,dc,L+L)'
PARTS=(LONG_PREFIX,'Sum(ab,ac,L,u)','Sum(bb,bc,L,v)','Sum(cb,cc,L,s)','Sum(cb,cc,L+L,t)','Le(s,u*v)','Le(u*v,t)')
NAMED_SOURCE='forall '+' '.join(P)+'. Le(L,M) -> exists cb cc u v s t. '+conjoin(PARTS)
TARGET_SHA256='f7b106d5f635ac96c28ef758a3a64c6f827875f97e9103f80b6f48ce84f679c5'
HELPER_SOURCES={
    'shorten':'forall b c L M. Le(L,M) -> forall j a. Lt(j,L) -> BetaZeroExtend(b,c,M,j,a) -> BetaZeroExtend(b,c,L,j,a)',
    'sum_prefix':'forall ab ac L M s t. Le(L,M) -> Sum(ab,ac,L,s) -> Sum(ab,ac,M,t) -> Le(s,t)',
    'low_coefficient':'forall '+' '.join(P+('i','a','b'))+'. Le(L,M) -> Lt(i,L) -> '+coefficient(C,D,'i','a')+' -> '+coefficient(A,B,'i','b')+' -> a=b',
    'bounds':'forall '+' '.join(P+('cb','cc','db','dc','s','r','z','t'))+'. Le(L,M) -> '+LONG_PREFIX+' -> '+SHORT_PREFIX+' -> Sum(cb,cc,L,s) -> Sum(db,dc,L,r) -> Sum(db,dc,L+L,z) -> Sum(cb,cc,L+L,t) -> Le(s,z) /\\ Le(z,t)',
}
HELPER_TARGET_SHA256={
    'shorten':'78de68ab736ede82dc5a311776d94186dd3fe5c1f53b5d2445eff8da8ffa427c',
    'sum_prefix':'e272f493342a6756bb7bd10dd5624536441f3549f8dcfbb7b4b20ac448e2270c',
    'low_coefficient':'2836b80cafdf902f4cf18c9a7075700deb52a12e47e3eac53c33d7cccdb1e524',
    'bounds':'94162a9baf7cc1c3f70c26aeee0abcd4c03f6f244f68ba734da146ddf72d4958'}
ORDER_ARCHIVE=dict(case='AP040',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-convolution-prefix-order-v1/generation-process.json.gz',
    bytes=40445,sha256='99cfb407882ac9f392f4d597ec4040e9662ae2e5ae9faae99ff43ebd840c0333',
    raw_bytes=270356,raw_sha256='f900fec8df5e28ae28a37276ebd9ef53389e3cfadce02071eef6ee695ce294f7',
    bundle_bytes=105513,bundle_sha256='aaac37a0c2c53902ca053f77467100e9b542536f01288e2ba1d04e158e54a5d2',
    nodes=46,root=45,target_ast_sha256='a4ddc6ed1dd2d269caed60e2cc1647676c11767abf060d3c1641e5d50ed1adb0')
INSIDE_ARCHIVE=dict(case='AP038',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-convolution-recurrence-v1/generation-process.json.gz',
    bytes=52480,sha256='e2130f230b3a4755cc1919caff75916cf0f4bf71c6f8925fafdb90725806eaf7',
    raw_bytes=707521,raw_sha256='52abb65f4017e7e0d6a3ce25cc038d7833042077c4bc647b0b3f698d53ef8b9f',
    bundle_bytes=392744,bundle_sha256='eb3ee35d22bb87a6c5ca3963644da32ed3fc677db0ee176185b032bb6c3910e2',
    nodes=147,root=146,target_ast_sha256='1d0487d27421420580ddbc9e31618cfe3a90ef13648ea8c02a25c5be0e87f7e0')
ARCHIVES=(ORDER_ARCHIVE,INSIDE_ARCHIVE,TOTAL_ARCHIVE,LOCAL_ARCHIVE,SPLIT_ARCHIVE,CONVOLUTION_ARCHIVE)
ENDPOINT_SOURCES={
    'le_refl':'forall a. Le(a,a)','le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'add_comm':'forall a b. a+b=b+a',
    'sum_exists':'forall b c N. exists n. Sum(b,c,N,n)',
    'sum_unique':'forall b c N n m. Sum(b,c,N,n) -> Sum(b,c,N,m) -> n=m',
    'coefficient_unique':CONVOLUTION_HELPERS['coefficient_unique'],
    'prefix_exists':CONVOLUTION_HELPERS['prefix_exists'],'prefix_entry':CONVOLUTION_HELPERS['prefix_entry'],
    'inside':EXP_HELPERS['inside'],'sum_order':ORDER_HELPERS['sum_order'],
    'coefficient_order':ORDER_SOURCE,'total':TOTAL_SOURCE,'locality':LOCAL_HELPERS['coefficient_transport'],
    'splitting':SPLIT_SOURCE,
}
ENDPOINT_OWNERS={name:'CV003' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(inside='AP038',sum_order='AP040',coefficient_order='AP040',total='CV048',locality='CV050',splitting='CV009')
HELPER_DEPENDENCIES={
    'shorten':('inside','le_trans'),
    'sum_prefix':('splitting','sum_unique','add_comm'),
    'low_coefficient':('shorten','locality','coefficient_unique'),
    'bounds':('prefix_entry','coefficient_order','low_coefficient','le_trans','le_refl','sum_order','sum_prefix'),
    'AP041':('total','prefix_exists','sum_exists','bounds'),
}


class ConvolutionSumSandwichError(ValueError):
    """Changed actual prefix, rectangular product, cutoff or ordered input."""


def definition_registry():
    pool=source_registry();needed=set();pending=['Le','NatConvolutionPrefix','NatAffineSum']
    while pending:
        name=pending.pop()
        if name not in needed:
            needed.add(name);pending.extend(pool[name].conceptual_dependencies)
    result={name:spec for name,spec in pool.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ConvolutionSumSandwichError('existing convolution-sum definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_convolution_sum_sandwich_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=6 or len(premises)!=1 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ConvolutionSumSandwichError('AP041 exact finite rectangular convolution sandwich changed')
    return target


def source_contract():
    return dict(code='AP041',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,input_length_order_required=True,both_actual_input_codes_preserved=True,
        long_input_convolution_and_all_four_sums_constructed=True,
        lower_output_length='L',upper_output_length='L+L',rectangular_input_lengths='L,L',
        finite_sandwich='sum(C,L)<=sum(A,L)*sum(B,L)<=sum(C,L+L)',
        empty_and_equal_input_lengths_allowed=True,new_induction_needed=False,new_induction_count=0,
        new_definition_ids=[],definition_admissions=0,quantitative_tail_bound=False,
        analytic_exponential_addition=False,analytic_limit_claim=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def convolution_sum_sandwich_source_pins():
    result=convolution_prefix_order_source_pins()
    for name,pin in exp_convolution_recurrence_source_pins().items():
        if name in result and result[name]!=pin:
            raise ConvolutionSumSandwichError('finite convolution sandwich source disagreement')
        result[name]=pin
    expected={'scripts/sqrt2_power_exp_convolution_recurrence.py':'363a4bbe814f00bc40656974bfee314128b4d50d5e8c5685c8914e8c04424845',
        'scripts/sqrt2_power_convolution_prefix_order.py':'5b7008d31e16436b2fa676075a8413cca714de5763f2fd0debdbdf2244e3f729',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_convolution_sum_sandwich.py'):
        with (ROOT/name).open('rb') as stream: raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ConvolutionSumSandwichError('convolution sandwich source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _shorten(s):
    from peano_lab.kernel.proofs import AndIntro,OrIntroL
    from peano_lab.kernel.terms import Succ
    def entry(t):
        L,M,j=t.terms(('L','M','j'))
        longer=apply(specialize(t,'le_trans',Succ(j),L,M),t.hyp('bound'),t.hyp('length'))
        actual=apply(specialize(t,'inside',*t.terms(('b','c','M','j','a'))),longer,t.hyp('padded'))
        return OrIntroL(AndIntro(t.hyp('bound'),actual))
    return introduce(s,('b','c','L','M'),('length',),lambda t:
        introduce(t,('j','a'),('bound','padded'),entry))


def _sum_prefix(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Add
    def chosen(t):
        L,k,s,u,v,w=t.terms(('L','k','s','u','v','w'));data=t.hyp('split')
        length=_chain(specialize(t,'add_comm',L,k),t.hyp('gap'))
        whole=_subst(t,registry,'Sum(ab,ac,slot,t)',EqSym(length),t.hyp('whole_sum'))
        first=apply(specialize(t,'sum_unique',*t.terms(('ab','ac','L','u','s'))),field(data,0,4),t.hyp('prefix_sum'))
        last=apply(specialize(t,'sum_unique',*t.terms(('ab','ac')),Add(L,k),*t.terms(('w','t'))),field(data,2,4),whole)
        equation=_chain(specialize(t,'add_comm',v,s),CongAdd(EqSym(first),EqRefl(v)),EqSym(field(data,3,4)),last)
        return witness((v,),equation)
    return introduce(s,('ab','ac','L','M','s','t'),('length','prefix_sum','whole_sum'),lambda t:
        eliminate(t,t.hyp('length'),('k',),'gap',lambda u:
            eliminate(u,specialize(u,'splitting',*u.terms(('ab','ac','L','k'))),('u','v','w'),'split',chosen)))


def _low_coefficient(s):
    def finish(t):
        L,M,i,a,b=t.terms(('L','M','i','a','b'))
        long=t.terms(('ab','ac'))+(M,)+t.terms(('bb','bc'))+(M,)
        short=t.terms(('ab','ac'))+(L,)+t.terms(('bb','bc'))+(L,)
        first=apply(specialize(t,'shorten',*t.terms(('ab','ac','L','M'))),t.hyp('length'))
        second=apply(specialize(t,'shorten',*t.terms(('bb','bc','L','M'))),t.hyp('length'))
        transported=apply(specialize(t,'locality',*(long+short+(L,i,a))),first,second,t.hyp('bound'),t.hyp('long_coefficient'))
        return apply(specialize(t,'coefficient_unique',*(short+(i,a,b))),transported,t.hyp('short_coefficient'))
    return introduce(s,P+('i','a','b'),('length','bound','long_coefficient','short_coefficient'),finish)


def _bounds(s,registry):
    from peano_lab.kernel.proofs import AndIntro,EqRefl
    from peano_lab.kernel.terms import Add,Succ
    def finish(t):
        L=t.term('L');width=Add(L,L)
        length=witness((L,),EqRefl(width))
        def low_point(u):
            i,a,b,L=u.terms(('i','a','b','L'));width=Add(L,L)
            broader=apply(specialize(u,'le_trans',Succ(i),L,width),u.hyp('bound'),witness((L,),EqRefl(width)))
            big=u.terms(('ab','ac','M','bb','bc','M','cb','cc'))+(width,i,a)
            small=u.terms(('ab','ac','L','bb','bc','L','db','dc'))+(width,i,b)
            high=apply(specialize(u,'prefix_entry',*big),u.hyp('long_prefix'),broader,u.hyp('long_entry'))
            low=apply(specialize(u,'prefix_entry',*small),u.hyp('short_prefix'),broader,u.hyp('short_entry'))
            same=apply(specialize(u,'low_coefficient',*u.terms(P+('i','a','b'))),u.hyp('length'),u.hyp('bound'),high,low)
            return _right(u,registry,specialize(u,'le_refl',a),a,same)
        def high_point(u):
            L,i,a,b=u.terms(('L','i','a','b'));width=Add(L,L)
            short=u.terms(('ab','ac','L','bb','bc','L','db','dc'))+(width,i,a)
            long=u.terms(('ab','ac','M','bb','bc','M','cb','cc'))+(width,i,b)
            low=apply(specialize(u,'prefix_entry',*short),u.hyp('short_prefix'),u.hyp('bound'),u.hyp('short_entry'))
            high=apply(specialize(u,'prefix_entry',*long),u.hyp('long_prefix'),u.hyp('bound'),u.hyp('long_entry'))
            return apply(specialize(u,'coefficient_order',*u.terms(('ab','ac','L','bb','bc','L','M','M','i','a','b'))),
                u.hyp('length'),u.hyp('length'),low,high)
        below=introduce(t,('i','a','b'),('bound','long_entry','short_entry'),low_point)
        above=introduce(t,('i','a','b'),('bound','short_entry','long_entry'),high_point)
        low=apply(specialize(t,'sum_order',*t.terms(('cb','cc','db','dc','L','s','r'))),below,t.hyp('long_short_sum'),t.hyp('short_short_sum'))
        middle=apply(specialize(t,'sum_prefix',*t.terms(('db','dc','L')),width,*t.terms(('r','z'))),
            length,t.hyp('short_short_sum'),t.hyp('short_whole_sum'))
        low=apply(specialize(t,'le_trans',*t.terms(('s','r','z'))),low,middle)
        high=apply(specialize(t,'sum_order',*t.terms(('db','dc','cb','cc')),width,*t.terms(('z','t'))),
            above,t.hyp('short_whole_sum'),t.hyp('long_whole_sum'))
        return AndIntro(low,high)
    return introduce(s,P+('cb','cc','db','dc','s','r','z','t'),
        ('length','long_prefix','short_prefix','long_short_sum','short_short_sum','short_whole_sum','long_whole_sum'),finish)


def _root(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Add
    def chosen(t):
        data=t.hyp('product_data');s,z=t.terms(('s','z'))
        bounds=apply(specialize(t,'bounds',*t.terms(P+('cb','cc','db','dc','s','r','z','t'))),
            t.hyp('length'),t.hyp('long_prefix'),field(data,0,5),t.hyp('long_short_sum'),
            t.hyp('short_short_sum'),field(data,3,5),t.hyp('long_whole_sum'))
        lower=_right(t,registry,AndElimL(bounds),s,field(data,4,5))
        upper=_left(t,registry,AndElimR(bounds),t.term('t'),field(data,4,5))
        return witness(t.terms(('cb','cc','u','v','s','t')),conjunction(t.hyp('long_prefix'),
            field(data,1,5),field(data,2,5),t.hyp('long_short_sum'),t.hyp('long_whole_sum'),lower,upper))
    def constructed(t):
        return eliminate(t,specialize(t,'sum_exists',*t.terms(('cb','cc','L'))),('s',),'long_short_sum',lambda u:
            eliminate(u,specialize(u,'sum_exists',*u.terms(('db','dc','L'))),('r',),'short_short_sum',lambda v:
                eliminate(v,specialize(v,'sum_exists',*v.terms(('cb','cc')),Add(v.term('L'),v.term('L'))),('t',),'long_whole_sum',chosen)))
    def total(t):
        L=t.term('L')
        return eliminate(t,specialize(t,'prefix_exists',*t.terms(('ab','ac','M','bb','bc','M')),Add(L,L)),('cb','cc'),'long_prefix',constructed)
    return introduce(s,P,('length',),lambda t:
        eliminate(t,specialize(t,'total',*t.terms(('ab','ac','L','bb','bc','L'))),('db','dc','u','v','z'),'product_data',total))


def prove_convolution_sum_sandwich(*,limits=None):
    registry=definition_registry()
    factories={'shorten':_shorten,'sum_prefix':lambda s:_sum_prefix(s,registry),'low_coefficient':_low_coefficient,
        'bounds':lambda s:_bounds(s,registry),'AP041':lambda s:_root(s,registry)}
    return assemble_mixed_certificate(code='AP041',target=frozen_convolution_sum_sandwich_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories=factories,pins=convolution_sum_sandwich_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
