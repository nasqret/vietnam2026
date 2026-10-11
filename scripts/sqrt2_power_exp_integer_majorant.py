"""AP072: a horizon-independent exponential-size bound at integer arguments.

Ordinary induction in L proves that every actual finite recurrence at L*d
has sum at most 9^(L+1) times its head. The successor constructs positive
tables at L*d and d and uses same-degree submultiplicativity. Only those
constructed heads are cancelled; the supplied head can be zero.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_exp_submultiplicative import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,canonical,json_hash,
    source_registry,exp_submultiplicative_source_pins,NAMED_SOURCE as PRODUCT_SOURCE,BOUND_ARCHIVE,
)
from sqrt2_power_scaled_exp_terms import NAMED_SOURCE as CONSTRUCTED_SOURCE,scaled_exp_terms_source_pins
from sqrt2_power_scaled_exp_bound import EXP_ARCHIVE,HELPER_SOURCES as SMALL_HELPERS
from sqrt2_power_positive_power_comparison import positive_power_comparison_source_pins
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-integer-majorant-v1'
PARAMETERS=('L','d','N','tb','tc','h','s','C')
ROW_PARAMETERS=PARAMETERS[1:]
PREMISES=('~d=0','NatScaledExpRecurrence(d,L*d,tb,tc,N)','BetaAt(tb,tc,0,h)','Sum(tb,tc,S N,s)','Pow(9,S L,C)')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> Le(s,C*h)'
TARGET_SHA256='0c8801ad08d671c34b8ab3b48766c6133267c4b5abfd1b796eb18c6422b8d237'
HELPER_SOURCES={'arithmetic':'forall a b h s u v p C. ~a=0 -> ~b=0 -> Le(u,p*a) -> Le(v,9*b) -> Le((a*b)*s,h*(u*v)) -> C=p*9 -> Le(s,C*h)'}
HELPER_TARGET_SHA256={'arithmetic':'0e510251548c547f203049a3d9e5515584fdb1b716acf1e9dc7fbbec1c7106d8'}
PRODUCT_ARCHIVE=dict(case='AP071',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-submultiplicative-v1/generation-process.json.gz',
    bytes=84825,sha256='47b0190182d319edee665bcef843414d51748864b4bf04d21a1c68d52680aa5d',
    raw_bytes=1494624,raw_sha256='3593914becb43f605b55784bc219de4fc734d4756942a563e636e41d9ec1284f',
    bundle_bytes=861106,bundle_sha256='9e82458eb38f49caf7d705ed9f288ba9de5be9b6e3884670b80be8a2c1b61d11',
    nodes=216,root=215,target_ast_sha256='172dd2d034e151140ec0f7866fbfea14a1de644c3bc4f01e38d61a48f66c9873')
POWER_ARCHIVE=dict(case='AP010',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-positive-power-comparison-v1/generation-process.json.gz',
    bytes=44957,sha256='953368beb1a180881e9ef3c6a465fce1dd7b5734b83d65065cabc8467065a919',
    raw_bytes=492979,raw_sha256='e3fff5d6253eb250a0b8270cdf73c812f6ecb6e19afb18789f08ad914558375b',
    bundle_bytes=258080,bundle_sha256='340b616e44a6822279a5bef8dc9bc4e8a15d748592e8b2870b82f50ffa1268fe',
    nodes=126,root=125,target_ast_sha256='4b0cf1709336ebd3b4aa2546b4ad7107701157fb692b6db7205344456192cd25')
ARCHIVES=(PRODUCT_ARCHIVE,EXP_ARCHIVE,POWER_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'product':PRODUCT_SOURCE,'constructed':CONSTRUCTED_SOURCE,'small_bound':SMALL_HELPERS['all_values'],
    'power_zero':'forall d n p. n=0 -> Pow(d,n,p) -> p=1',
    'power_step':'forall d n sn p. sn=S n -> Pow(d,sn,p) -> exists q. Pow(d,n,q) /\\ p=q*d',
    'mul_ne_zero':'forall a b. ~a=0 -> ~b=0 -> ~(a*b)=0',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'mul_right_mono':'forall a b c. Le(a,b) -> Le(a*c,b*c)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)','mul_comm':'forall a b. a*b=b*a',
    'one_mul':'forall a. 1*a=a','zero_mul':'forall a. 0*a=0',
    'zero_le':'forall a. Le(0,a)','mul_succ_left':'forall a b. (S a)*b=a*b+b',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'mul_le_cancel':'forall c a b. ~c=0 -> Le(c*a,c*b) -> Le(a,b)'}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(product='AP071',constructed='CV070',power_zero='AP010',power_step='AP010')
HELPER_DEPENDENCIES={'arithmetic':('mul_ne_zero','mul_left_mono','mul_right_mono','mul_assoc','mul_comm','le_trans','mul_le_cancel'),
    'AP072':('product','constructed','small_bound','power_zero','power_step','one_mul','zero_mul','zero_le','mul_succ_left','arithmetic')}
FIRST_OUTPUTS=('aw','az','ab','ac','a','af','aq','u')
SECOND_OUTPUTS=('bw','bz','bb','bc','b','bf','bq','v')
ROW_HYPS=('nonzero','recurrence','head','sum','power')


class ExpIntegerMajorantError(ValueError):
    """Changed uniform finite bound, induction or actual positive witnesses."""


def definition_registry():
    pool=source_registry();needed=set();pending=['Le','Sum','NatScaledExpRecurrence','Pow','NatExpWeightTable','NatPowerWeightedPrefix','Factorial']
    while pending:
        name=pending.pop()
        if name not in needed:needed.add(name);pending.extend(pool[name].conceptual_dependencies)
    result={name:spec for name,spec in pool.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ExpIntegerMajorantError('integer-majorant conservative definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_exp_integer_majorant_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=8 or len(premises)!=5 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpIntegerMajorantError('AP072 exact all-horizon integer-argument majorant changed')
    return target


def source_contract():
    return dict(code='AP072',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=5,actual_recurrence_head_sum_and_power_preserved=True,
        argument_numerator='L*d',supplied_power='C=9^(L+1)',bound='s<=C*h',
        uniform_in_finite_horizon=True,majorant_independent_of_argument_denominator=True,
        positive_successor_factor_tables_constructed=True,only_constructed_head_product_cancelled=True,
        zero_argument_supplied_head_and_horizon_allowed=True,new_induction_needed=True,new_induction_count=1,
        new_definition_ids=[],definition_admissions=0,large_ground_power_materialized=False,
        analytic_exponential_claimed=False,fixed_approximation_program_changed=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_integer_majorant_source_pins():
    result=exp_submultiplicative_source_pins()
    for source in (scaled_exp_terms_source_pins,positive_power_comparison_source_pins):
        for name,pin in source().items():
            if name in result and result[name]!=pin:raise ExpIntegerMajorantError('integer-majorant dependency source disagreement')
            result[name]=pin
    expected={'scripts/sqrt2_power_exp_submultiplicative.py':'6426b351fdd00688862b6936b6c39d8b0bf1510ee9615d599559bc66a6659d8d',
        'scripts/sqrt2_power_scaled_exp_terms.py':'329c4e741b144823db7d43c018756dd19033aa5beca1505b5f4d05ae7cbe316a',
        'scripts/sqrt2_power_scaled_exp_bound.py':'717128c4845645cca66209b12512d4de2905d6ecc4eebad8c04c197647f9ee0c',
        'scripts/sqrt2_power_positive_power_comparison.py':'381cd294ff30012ed53978ec2590eb3d8da009339ea342af90fa3ec876bbebd4',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_integer_majorant.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpIntegerMajorantError('integer-majorant source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _nine():
    from peano_lab.kernel.terms import Succ,Zero
    result=Zero()
    for _ in range(9):result=Succ(result)
    return result


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul
    nine=_nine()
    def finish(t):
        a,b,h,out,u,v,p,C=t.terms(('a','b','h','s','u','v','p','C'));pa=Mul(p,a);nb=Mul(nine,b);ab=Mul(a,b)
        first=apply(specialize(t,'mul_right_mono',u,pa,v),t.hyp('first_bound'))
        second=apply(specialize(t,'mul_left_mono',v,nb,pa),t.hyp('second_bound'))
        bound=apply(specialize(t,'le_trans',Mul(u,v),Mul(pa,v),Mul(pa,nb)),first,second)
        bound=apply(specialize(t,'mul_left_mono',Mul(u,v),Mul(pa,nb),h),bound)
        normalized=_chain(_multiplicative_equal(t,Mul(h,Mul(pa,nb)),Mul(ab,Mul(Mul(p,nine),h))),
            CongMul(EqRefl(ab),CongMul(EqSym(t.hyp('next_power')),EqRefl(h))))
        bound=_subst(t,registry,'Le(h*(u*v),slot)',normalized,bound)
        bound=apply(specialize(t,'le_trans',Mul(ab,out),Mul(h,Mul(u,v)),Mul(ab,Mul(C,h))),t.hyp('product_bound'),bound)
        positive=apply(specialize(t,'mul_ne_zero',a,b),t.hyp('first_positive'),t.hyp('second_positive'))
        return apply(specialize(t,'mul_le_cancel',ab,out,Mul(C,h)),positive,bound)
    return introduce(s,('a','b','h','s','u','v','p','C'),('first_positive','second_positive','first_bound','second_bound','product_bound','next_power'),finish)


def _root(s,target,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongAdd,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    one=Succ(Zero());two=Succ(one);nine=_nine()
    def base_chosen(t):
        d,N,h,out,C,p=t.terms(('d','N','h','s','C','p'));data=t.hyp('power_data')
        p1=apply(specialize(t,'power_zero',nine,Zero(),p),EqRefl(Zero()),AndElimL(data))
        exact=_chain(AndElimR(data),CongMul(p1,EqRefl(nine)),specialize(t,'one_mul',nine))
        bound=_subst(t,registry,'Le(slot,2*d)',EqSym(specialize(t,'zero_mul',d)),specialize(t,'zero_le',Mul(two,d)))
        small=apply(specialize(t,'small_bound',d,Mul(Zero(),d),N,*t.terms(('tb','tc')),h,out),
            t.hyp('nonzero'),bound,t.hyp('recurrence'),t.hyp('head'),t.hyp('sum'))
        return _subst(t,registry,'Le(s,slot*h)',EqSym(exact),small)
    def base(t):
        return eliminate(t,apply(specialize(t,'power_step',nine,Zero(),one,t.term('C')),EqRefl(one),t.hyp('power')),
            ('p',),'power_data',base_chosen)
    def finish(t):
        k,d,N,h,out,C,p,a,b,u,v=t.terms(('k','d','N','h','s','C','p','a','b','u','v'))
        first,second=t.hyp('first_data'),t.hyp('second_data')
        old=apply(specialize(t,'IH',d,N,*t.terms(('ab','ac')),a,u,p),t.hyp('nonzero'),field(first,9,11),field(first,3,11),field(first,8,11),AndElimL(t.hyp('power_data')))
        twice=_chain(specialize(t,'mul_succ_left',one,d),CongAdd(specialize(t,'one_mul',d),EqRefl(d)))
        unit_bound=witness((d,),EqSym(twice))
        unit=apply(specialize(t,'small_bound',d,d,N,*t.terms(('bb','bc')),b,v),t.hyp('nonzero'),unit_bound,field(second,9,11),field(second,3,11),field(second,8,11))
        recurrence=_subst(t,registry,'NatScaledExpRecurrence(d,slot,tb,tc,N)',specialize(t,'mul_succ_left',k,d),t.hyp('recurrence'))
        product=apply(specialize(t,'product',d,Mul(k,d),d,N,*t.terms(('ab','ac','bb','bc','tb','tc')),a,b,h,u,v,out),
            t.hyp('nonzero'),field(first,9,11),field(second,9,11),recurrence,
            field(first,3,11),field(second,3,11),t.hyp('head'),field(first,8,11),field(second,8,11),t.hyp('sum'))
        return apply(specialize(t,'arithmetic',a,b,h,out,u,v,p,C),field(first,4,11),field(second,4,11),old,unit,product,AndElimR(t.hyp('power_data')))
    def first(t):
        return eliminate(t,apply(specialize(t,'constructed',t.term('d'),t.term('d'),t.term('N')),t.hyp('nonzero')),SECOND_OUTPUTS,'second_data',finish)
    def powered(t):
        return eliminate(t,apply(specialize(t,'constructed',t.term('d'),Mul(t.term('k'),t.term('d')),t.term('N')),t.hyp('nonzero')),FIRST_OUTPUTS,'first_data',first)
    def successor(t):
        exponent=Succ(t.term('k'))
        return eliminate(t,apply(specialize(t,'power_step',nine,exponent,Succ(exponent),t.term('C')),EqRefl(Succ(exponent)),t.hyp('power')),('p',),'power_data',powered)
    return Ind(target.body,introduce(s,ROW_PARAMETERS,ROW_HYPS,base),
        introduce(s,('k',),('IH',),lambda t:introduce(t,ROW_PARAMETERS,ROW_HYPS,successor)))


def prove_exp_integer_majorant(*,limits=None):
    registry=definition_registry();target=frozen_exp_integer_majorant_target(_registry=registry)
    return assemble_mixed_certificate(code='AP072',target=target,registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'arithmetic':lambda s:_arithmetic(s,registry),'AP072':lambda s:_root(s,target,registry)},
        pins=exp_integer_majorant_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
