"""AP078: actual natural powers preserve products, including exponent zero.

Construct previous actual powers, identify each supplied successor through
power uniqueness, and use ordinary induction plus checked AC equalities.
The successor-value helper is retained as actual reusable proof data.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_positive_power_comparison import (
    ROOT,Scope,introduce,eliminate,apply,specialize,canonical,json_hash,
    definition_registry as power_registry,positive_power_comparison_source_pins,BOUND_ARCHIVE,
)
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-product-power-v1'
PARAMETERS=('k','a','b','u','v','w')
PREMISES=('Pow(a,k,u)','Pow(b,k,v)','Pow(a*b,k,w)')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> w=u*v'
TARGET_SHA256='5f37e55e15971ec0ef5bcf1a9435c0ed369dbe1f3b53b3fa089c6e8ee4a2294c'
HELPER_SOURCES={'successor_value':'forall a k p q. Pow(a,k,p) -> Pow(a,S k,q) -> q=p*a'}
HELPER_TARGET_SHA256={'successor_value':'2cf1d8baecbeae841376f4539e07083ac532574d57083de49a47f6adc6b0e1ff'}
POWER_ARCHIVE=dict(case='AP010',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-positive-power-comparison-v1/generation-process.json.gz',
    bytes=44957,sha256='953368beb1a180881e9ef3c6a465fce1dd7b5734b83d65065cabc8467065a919',
    raw_bytes=492979,raw_sha256='e3fff5d6253eb250a0b8270cdf73c812f6ecb6e19afb18789f08ad914558375b',
    bundle_bytes=258080,bundle_sha256='340b616e44a6822279a5bef8dc9bc4e8a15d748592e8b2870b82f50ffa1268fe',
    nodes=126,root=125,target_ast_sha256='4b0cf1709336ebd3b4aa2546b4ad7107701157fb692b6db7205344456192cd25')
ARCHIVES=(POWER_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'power_zero':'forall d n p. n=0 -> Pow(d,n,p) -> p=1',
    'power_step':'forall d n sn p. sn=S n -> Pow(d,sn,p) -> exists q. Pow(d,n,q) /\\ p=q*d',
    'power_exists':'forall a n. exists p. Pow(a,n,p)',
    'power_unique':'forall a n x y. Pow(a,n,x) -> Pow(a,n,y) -> x=y',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)','mul_comm':'forall a b. a*b=b*a','one_mul':'forall a. 1*a=a'}
ENDPOINT_OWNERS={name:('AP010' if name.startswith('power_') else 'CV071') for name in ENDPOINT_SOURCES}
HELPER_DEPENDENCIES={'successor_value':('power_step','power_unique'),
    'AP078':('power_zero','power_exists','successor_value','mul_assoc','mul_comm','one_mul')}


class ProductPowerError(ValueError):
    """Changed actual base product, exponent or value identity."""


def definition_registry():
    source=power_registry();result={name:spec for name,spec in source.items() if name!='Le'};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:raise ProductPowerError('product-power conservative definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_product_power_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Eq
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=6 or len(premises)!=3 or type(conclusion) is not Eq or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ProductPowerError('AP078 exact actual power-product identity changed')
    return target


def source_contract():
    return dict(code='AP078',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=3,all_three_actual_powers_preserved=True,value_identity='(a*b)^k=a^k*b^k',
        zero_bases_and_exponent_allowed=True,positive_bases_required=False,actual_previous_powers_constructed=True,
        actual_successor_values_identified_by_uniqueness=True,code_number_equality_claimed=False,
        new_induction_needed=True,new_induction_count=1,new_definition_ids=[],definition_admissions=0,
        analytic_power_claimed=False,fixed_approximation_program_changed=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def product_power_source_pins():
    result=positive_power_comparison_source_pins()
    expected={'scripts/sqrt2_power_positive_power_comparison.py':'381cd294ff30012ed53978ec2590eb3d8da009339ea342af90fa3ec876bbebd4',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in ('scripts/sqrt2_power_finite_power_evaluation.py','scripts/sqrt2_power_quadratic_height.py','scripts/sqrt2_power_mixed_assembly.py'):
        if name not in result:raise ProductPowerError('unbound imported proof constructor source: '+name)
    for name in (*expected,'scripts/sqrt2_power_product_power.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:raise ProductPowerError('product-power source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _successor_value(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongMul,EqRefl
    from peano_lab.kernel.terms import Succ
    def chosen(t):
        a,k,p,q,x=t.terms(('a','k','p','q','x'));data=t.hyp('step')
        same=apply(specialize(t,'power_unique',a,k,x,p),AndElimL(data),t.hyp('previous_power'))
        return _chain(AndElimR(data),CongMul(same,EqRefl(a)))
    def finish(t):
        a,k,q=t.terms(('a','k','q'))
        return eliminate(t,apply(specialize(t,'power_step',a,k,Succ(k),q),EqRefl(Succ(k)),t.hyp('next_power')),('x',),'step',chosen)
    return introduce(s,('a','k','p','q'),('previous_power','next_power'),finish)


def _root(s,target):
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Mul,Succ,Zero
    zero=Zero();one=Succ(zero);rows=PARAMETERS[1:];hyps=('power_a','power_b','power_product')
    def base(t):
        a,b,u,v,w=t.terms(rows)
        p1=apply(specialize(t,'power_zero',a,zero,u),EqRefl(zero),t.hyp('power_a'))
        q1=apply(specialize(t,'power_zero',b,zero,v),EqRefl(zero),t.hyp('power_b'))
        r1=apply(specialize(t,'power_zero',Mul(a,b),zero,w),EqRefl(zero),t.hyp('power_product'))
        return _chain(r1,EqSym(_chain(CongMul(p1,q1),specialize(t,'one_mul',one))))
    def chosen(t):
        k,a,b,u,v,w,U,V,W=t.terms(PARAMETERS+('U','V','W'));ab=Mul(a,b)
        old=apply(specialize(t,'IH',a,b,U,V,W),t.hyp('previous_a'),t.hyp('previous_b'),t.hyp('previous_product'))
        ua=apply(specialize(t,'successor_value',a,k,U,u),t.hyp('previous_a'),t.hyp('power_a'))
        vb=apply(specialize(t,'successor_value',b,k,V,v),t.hyp('previous_b'),t.hyp('power_b'))
        wc=apply(specialize(t,'successor_value',ab,k,W,w),t.hyp('previous_product'),t.hyp('power_product'))
        return _chain(wc,CongMul(old,EqRefl(ab)),
            _multiplicative_equal(t,Mul(Mul(U,V),ab),Mul(Mul(U,a),Mul(V,b))),CongMul(EqSym(ua),EqSym(vb)))
    def second(t):
        return eliminate(t,specialize(t,'power_exists',Mul(t.term('a'),t.term('b')),t.term('k')),('W',),'previous_product',chosen)
    def first(t):
        return eliminate(t,specialize(t,'power_exists',t.term('b'),t.term('k')),('V',),'previous_b',second)
    def successor(t):
        return eliminate(t,specialize(t,'power_exists',t.term('a'),t.term('k')),('U',),'previous_a',first)
    return Ind(target.body,introduce(s,rows,hyps,base),
        introduce(s,('k',),('IH',),lambda t:introduce(t,rows,hyps,successor)))


def prove_product_power(*,limits=None):
    registry=definition_registry();target=frozen_product_power_target(_registry=registry)
    return assemble_mixed_certificate(code='AP078',target=target,registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'successor_value':_successor_value,'AP078':lambda s:_root(s,target)},
        pins=product_power_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
