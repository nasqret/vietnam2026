"""AP076: an ordered power-difference bound for actual natural powers.

One ordinary induction proves b^(k+1)<=a^(k+1)+(k+1)*g*M^k from
b=a+g and b<=M. Zero bases, zero gap and k=0 remain in the statement.
All three powers are supplied actual computations, not semantic axioms.
"""
from hashlib import sha256

from sqrt2_power_positive_power_comparison import (
    ROOT,Scope,introduce,eliminate,witness,apply,specialize,canonical,json_hash,
    definition_registry,positive_power_comparison_source_pins,BOUND_ARCHIVE,
    HELPER_SOURCES as COMPARISON_HELPERS,
)
from sqrt2_power_exp_two_sided_continuity import _left,_right
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-ordered-power-difference-v1'
PARAMETERS=('a','b','M','g','k','u','v','w')
PREMISES=('b=a+g','Le(b,M)','Pow(a,S k,u)','Pow(b,S k,v)','Pow(M,k,w)')
CONCLUSION='Le(v,u+(S k)*(g*w))'
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> '+CONCLUSION
TARGET_SHA256='d4d5beb6c20b976f94c1c1e219e65c4389e0dddce29a5b2f642ed9c3014a7b04'
HELPER_SOURCES={
    'power_one':'forall a p. Pow(a,1,p) -> p=a',
    'arithmetic':'forall a b M g j U V W w. b=a+g -> Le(b,M) -> Le(U,w) -> Le(V,U+j*(g*W)) -> w=W*M -> Le(V*b,U*a+(S j)*(g*w))',
}
HELPER_TARGET_SHA256={'power_one':'d02076c3c19a03538d28a73c30b20deee49c1d441f1ff16fbe18d356a1da0b9a',
    'arithmetic':'b08d57842bbfb5325fd924543145edd55c8836fc3e2264870f3d79ad49f2e55d'}
POWER_ARCHIVE=dict(case='AP010',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-positive-power-comparison-v1/generation-process.json.gz',
    bytes=44957,sha256='953368beb1a180881e9ef3c6a465fce1dd7b5734b83d65065cabc8467065a919',
    raw_bytes=492979,raw_sha256='e3fff5d6253eb250a0b8270cdf73c812f6ecb6e19afb18789f08ad914558375b',
    bundle_bytes=258080,bundle_sha256='340b616e44a6822279a5bef8dc9bc4e8a15d748592e8b2870b82f50ffa1268fe',
    nodes=126,root=125,target_ast_sha256='4b0cf1709336ebd3b4aa2546b4ad7107701157fb692b6db7205344456192cd25')
ARCHIVES=(POWER_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={
    'base_monotone':COMPARISON_HELPERS['base_monotone'],
    'power_zero':'forall d n p. n=0 -> Pow(d,n,p) -> p=1',
    'power_step':'forall d n sn p. sn=S n -> Pow(d,sn,p) -> exists q. Pow(d,n,q) /\\ p=q*d',
    'le_refl':'forall a. Le(a,a)','le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'mul_right_mono':'forall a b c. Le(a,b) -> Le(a*c,b*c)',
    'add_left_mono':'forall a b c. Le(a,b) -> Le(c+a,c+b)',
    'add_right_mono':'forall a b c. Le(a,b) -> Le(a+c,b+c)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)','mul_comm':'forall a b. a*b=b*a',
    'mul_add':'forall a b c. a*(b+c)=a*b+a*c','add_mul':'forall a b c. (a+b)*c=a*c+b*c',
    'add_assoc':'forall a b c. (a+b)+c=a+(b+c)','add_comm':'forall a b. a+b=b+a',
    'mul_succ_left':'forall a b. (S a)*b=a*b+b','one_mul':'forall a. 1*a=a',
}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(base_monotone='AP010',power_zero='AP010',power_step='AP010')
HELPER_DEPENDENCIES={
    'power_one':('power_zero','power_step','one_mul'),
    'arithmetic':('mul_left_mono','mul_right_mono','add_left_mono','add_right_mono','le_trans',
        'mul_assoc','mul_comm','mul_add','add_mul','add_assoc','add_comm','mul_succ_left'),
    'AP076':('power_one','power_zero','power_step','base_monotone','arithmetic','le_refl','le_trans','add_comm','one_mul','mul_comm'),
}


class OrderedPowerDifferenceError(ValueError):
    """Changed ordered gap, actual exponent or power-difference coefficient."""


def frozen_ordered_power_difference_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=8 or len(premises)!=5 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise OrderedPowerDifferenceError('AP076 exact ordered power-difference target changed')
    return target


def source_contract():
    return dict(code='AP076',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=5,all_three_actual_powers_preserved=True,ordered_gap='b=a+g',upper_bound='b<=M',
        exponent='k+1',error_bound='(k+1)*g*M^k',zero_bases_gap_bound_and_k_allowed=True,
        positive_bases_required=False,division_or_denominator_cancellation_used=False,
        new_induction_needed=True,new_induction_count=1,new_definition_ids=[],definition_admissions=0,
        analytic_power_or_exponential_claimed=False,fixed_approximation_program_changed=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def ordered_power_difference_source_pins():
    result=positive_power_comparison_source_pins()
    expected={'scripts/sqrt2_power_positive_power_comparison.py':'381cd294ff30012ed53978ec2590eb3d8da009339ea342af90fa3ec876bbebd4',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in ('scripts/sqrt2_power_exp_two_sided_continuity.py','scripts/sqrt2_power_convolution_unit.py',
                 'scripts/sqrt2_power_finite_power_evaluation.py','scripts/sqrt2_power_quadratic_height.py','scripts/sqrt2_power_mixed_assembly.py'):
        if name not in result:raise OrderedPowerDifferenceError('unbound imported proof constructor source: '+name)
    for name in (*expected,'scripts/sqrt2_power_ordered_power_difference.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise OrderedPowerDifferenceError('ordered power-difference source or archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _power_one(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongMul,EqRefl
    from peano_lab.kernel.terms import Succ,Zero
    zero=Zero();one=Succ(zero)
    def chosen(t):
        a,p,q=t.terms(('a','p','q'));data=t.hyp('previous')
        q1=apply(specialize(t,'power_zero',a,zero,q),EqRefl(zero),AndElimL(data))
        return _chain(AndElimR(data),CongMul(q1,EqRefl(a)),specialize(t,'one_mul',a))
    def finish(t):
        return eliminate(t,apply(specialize(t,'power_step',t.term('a'),zero,one,t.term('p')),EqRefl(one),t.hyp('power')),('q',),'previous',chosen)
    return introduce(s,('a','p'),('power',),finish)


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ
    def finish(t):
        a,b,M,g,j,U,V,W,w=t.terms(('a','b','M','g','j','U','V','W','w'))
        Ua,Ub,Ug,wg=Mul(U,a),Mul(U,b),Mul(U,g),Mul(w,g)
        old_error=Mul(Mul(j,Mul(g,W)),b);new_error=Mul(j,Mul(g,w))
        result=apply(specialize(t,'mul_right_mono',V,Add(U,Mul(j,Mul(g,W))),b),t.hyp('previous_bound'))
        result=_right(t,registry,result,Mul(V,b),specialize(t,'add_mul',U,Mul(j,Mul(g,W)),b))
        first=apply(specialize(t,'mul_right_mono',U,w,g),t.hyp('power_bound'))
        first=apply(specialize(t,'add_left_mono',Ug,wg,Ua),first)
        first=_left(t,registry,first,Add(Ua,wg),EqSym(_chain(CongMul(EqRefl(U),t.hyp('gap')),specialize(t,'mul_add',U,a,g))))
        second=apply(specialize(t,'mul_left_mono',b,M,W),t.hyp('base_bound'))
        second=_right(t,registry,second,Mul(W,b),EqSym(t.hyp('next_power')))
        second=apply(specialize(t,'mul_left_mono',Mul(W,b),w,Mul(j,g)),second)
        second=_left(t,registry,second,Mul(Mul(j,g),w),_multiplicative_equal(t,Mul(Mul(j,g),Mul(W,b)),old_error))
        second=_right(t,registry,second,old_error,specialize(t,'mul_assoc',j,g,w))
        first=apply(specialize(t,'add_right_mono',Ub,Add(Ua,wg),old_error),first)
        second=apply(specialize(t,'add_left_mono',old_error,new_error,Add(Ua,wg)),second)
        combined=apply(specialize(t,'le_trans',Add(Ub,old_error),Add(Add(Ua,wg),old_error),Add(Add(Ua,wg),new_error)),first,second)
        result=apply(specialize(t,'le_trans',Mul(V,b),Add(Ub,old_error),Add(Add(Ua,wg),new_error)),result,combined)
        coefficient=_chain(CongAdd(specialize(t,'mul_comm',w,g),EqRefl(new_error)),
            specialize(t,'add_comm',Mul(g,w),new_error),EqSym(specialize(t,'mul_succ_left',j,Mul(g,w))))
        exact=_chain(specialize(t,'add_assoc',Ua,wg,new_error),CongAdd(EqRefl(Ua),coefficient))
        return _right(t,registry,result,Mul(V,b),exact)
    return introduce(s,('a','b','M','g','j','U','V','W','w'),('gap','base_bound','power_bound','previous_bound','next_power'),finish)


def _root(s,target,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongAdd,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    zero=Zero();one=Succ(zero);rows=('u','v','w');hyps=('gap','base_bound','power_a','power_b','power_M')
    def base(t):
        a,b,M,g,u,v,w=t.terms(('a','b','M','g','u','v','w'))
        ua=apply(specialize(t,'power_one',a,u),t.hyp('power_a'))
        vb=apply(specialize(t,'power_one',b,v),t.hyp('power_b'))
        w1=apply(specialize(t,'power_zero',M,zero,w),EqRefl(zero),t.hyp('power_M'))
        error=_chain(specialize(t,'one_mul',Mul(g,w)),CongMul(EqRefl(g),w1),specialize(t,'mul_comm',g,one),specialize(t,'one_mul',g))
        rhs=CongAdd(ua,error)
        exact=_chain(vb,t.hyp('gap'),EqSym(rhs))
        return _right(t,registry,specialize(t,'le_refl',v),v,exact)
    def chosen(t):
        a,b,M,g,k,u,v,w,U,V,W=t.terms(('a','b','M','g','k','u','v','w','U','V','W'));sk=Succ(k)
        pa,pb,pm=t.hyp('previous_a'),t.hyp('previous_b'),t.hyp('previous_M')
        old=apply(specialize(t,'IH',U,V,W),t.hyp('gap'),t.hyp('base_bound'),AndElimL(pa),AndElimL(pb),AndElimL(pm))
        ordered=witness((g,),_chain(specialize(t,'add_comm',g,a),EqSym(t.hyp('gap'))))
        bounded=apply(specialize(t,'le_trans',a,b,M),ordered,t.hyp('base_bound'))
        power_bound=apply(instantiate(apply(specialize(t,'base_monotone',a,M),bounded),sk,U,w),AndElimL(pa),t.hyp('power_M'))
        result=apply(specialize(t,'arithmetic',a,b,M,g,sk,U,V,W,w),t.hyp('gap'),t.hyp('base_bound'),power_bound,old,AndElimR(pm))
        result=_subst(t,registry,'Le(slot,U*a+(S(S k))*(g*w))',EqSym(AndElimR(pb)),result)
        return _subst(t,registry,'Le(v,slot+(S(S k))*(g*w))',EqSym(AndElimR(pa)),result)
    def second(t):
        k=t.term('k')
        return eliminate(t,apply(specialize(t,'power_step',t.term('M'),k,Succ(k),t.term('w')),EqRefl(Succ(k)),t.hyp('power_M')),('W',),'previous_M',chosen)
    def first(t):
        sk=Succ(t.term('k'))
        return eliminate(t,apply(specialize(t,'power_step',t.term('b'),sk,Succ(sk),t.term('v')),EqRefl(Succ(sk)),t.hyp('power_b')),('V',),'previous_b',second)
    def successor(t):
        sk=Succ(t.term('k'))
        return eliminate(t,apply(specialize(t,'power_step',t.term('a'),sk,Succ(sk),t.term('u')),EqRefl(Succ(sk)),t.hyp('power_a')),('U',),'previous_a',first)
    motive=target
    for _ in range(5):motive=motive.body
    return introduce(s,PARAMETERS[:4],(),lambda t:Ind(motive,introduce(t,rows,hyps,base),
        introduce(t,('k',),('IH',),lambda u:introduce(u,rows,hyps,successor))))


def prove_ordered_power_difference(*,limits=None):
    registry=definition_registry();target=frozen_ordered_power_difference_target(_registry=registry)
    return assemble_mixed_certificate(code='AP076',target=target,registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'power_one':_power_one,'arithmetic':lambda s:_arithmetic(s,registry),'AP076':lambda s:_root(s,target,registry)},
        pins=ordered_power_difference_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
