"""AP082: supplied logarithm/exponential refinement with two explicit errors.

Use actual independent atanh and Horner computations, extract their ordered
cross-product gap, and apply the unit-argument finite exponential estimate.
Cancel only the proved positive coefficient/denominator factor. No limit,
code equality, special choice of normalization or fixed-program change.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_argument_modulus import (
    ROOT,Scope,introduce,apply,specialize,canonical,json_hash,
    definition_registry as argument_registry,argument_modulus_source_pins,LOG_ARCHIVE,
    ENDPOINT_SOURCES as ARGUMENT_ENDPOINTS,HELPER_SOURCES as ARGUMENT_HELPERS,
)
from sqrt2_power_exp_two_error_bound import (
    NAMED_SOURCE as TWO_ERROR_SOURCE,definition_registry as exp_registry,
    exp_two_error_bound_source_pins,BOUND_ARCHIVE,
)
from sqrt2_power_independent_atanh_truncation import NAMED_SOURCE as LOG_SOURCE
from sqrt2_power_ternary_atanh_bound import NAMED_SOURCE as INNER_SOURCE
from sqrt2_power_ternary_prefix_bound import TERNARY_ARCHIVE
from sqrt2_power_exp_two_sided_continuity import (
    HELPER_SOURCES as ORDER_HELPERS,exp_two_sided_continuity_source_pins,_left,_right,
)
from sqrt2_power_quadratic_trace_exists import eliminate,conjunction,field
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-log-exp-refinement-v1'
PARAMETERS=('d','e','ab','ac','bb','bc','k','l','x','z','p','q','m','N','cb','cc','eb','ec','a0','b0','u','v','P')
PREMISES=('~d=0','~e=0','NatAtanhPrefix(d,ab,ac,S k)','NatAtanhPrefix(e,bb,bc,(S k)+l)',
    'NatHornerValue(ab,ac,3,S k,x)','NatHornerValue(bb,bc,3,(S k)+l,z)',
    'Pow(3,S k,p)','Pow(3,(S k)+l,q)',
    'NatScaledExpRecurrence(d*p,3*x,cb,cc,m)','NatScaledExpRecurrence(e*q,3*z,eb,ec,(S m)+N)',
    'BetaAt(cb,cc,0,a0)','BetaAt(eb,ec,0,b0)','Sum(cb,cc,S m,u)','Sum(eb,ec,S((S m)+N),v)','Pow(2,m,P)')
BOUND='Le((p*P)*(a0*v),(p*P)*(b0*u)+((9*3)*P+2*p)*(a0*b0))'
CONCLUSION='~p=0 /\\ (~q=0 /\\ (~P=0 /\\ (~(d*p)=0 /\\ (~(e*q)=0 /\\ (Le(b0*u,a0*v) /\\ '+BOUND+')))))'
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> '+CONCLUSION
TARGET_SHA256='bccfdfa515c324f3b34a5a205185f1a81d590d8d27d1b41dcba91fbbd65883cc'
HELPER_SOURCES={'arithmetic':'forall F p P g a b u v. ~F=0 -> Le(g,3*F) -> Le((p*F)*(P*(a*v)),(p*F)*(P*(b*u))+(9*(g*P)+2*(p*F))*(a*b)) -> Le((p*P)*(a*v),(p*P)*(b*u)+((9*3)*P+2*p)*(a*b))'}
HELPER_TARGET_SHA256={'arithmetic':'63513b9afe3e4c2c99e4b07e836042b1f2832c735ec5dafeebf8e7384ca59d51'}
TWO_ERROR_ARCHIVE=dict(case='CV101',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-two-error-bound-v2/generation-process.json.gz',
    bytes=53195,sha256='1bfee7ad54dd54e433b84c99a5d975b165b626581dcd7ab4ce8cd2524af3cfad',
    raw_bytes=1042578,raw_sha256='82626da5c3d58fafe1f4faa83c00522fc56fea068a06c82fb541abebbe9d460d',
    bundle_bytes=613675,bundle_sha256='ac305ff130d7a1936202c1022e0aa06acc322a556ae0d6684918bc30cb5533bd',
    nodes=189,root=188,target_ast_sha256='99e2c67d567497309e07b57a9c96266fe4299a7a38f24bf605373710dc0b6857')
ARGUMENT_ARCHIVE=dict(case='AP006',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-argument-modulus-v1/generation-process.json.gz',
    bytes=63074,sha256='30590e98578f0d7b245cad99aed5b19c653d41b1ba6841846d59ad1c87a5e0de',
    raw_bytes=1029198,raw_sha256='6adfc247aace94ce0ed458f8270756b061f3eb22a1c174dc58b1346badf68cc8',
    bundle_bytes=595548,bundle_sha256='bf75787641e08251020beebea70fd3b959a6a124299bc6912608463dd6d8bb41',
    nodes=188,root=187,target_ast_sha256='cbc032a1e559ba87536c09544a5f7e321cc43378460e87bddebc0cb65a85584c')
ORDER_ARCHIVE=dict(case='AP007',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-two-sided-continuity-v1/generation-process.json.gz',
    bytes=44186,sha256='a7054532adf6a26abc55c5abef8c4c7aa7961699d2de5164336b3bba5bd5b0cb',
    raw_bytes=831759,raw_sha256='1126098f18ff1c50d381e6f36451f8daf3883df8144fbeba52a601e5e7a0225e',
    bundle_bytes=483848,bundle_sha256='147d7fa32b4cefb244f3a689bf9241c30b0170bc7eb867723c690751b82423bc',
    nodes=164,root=163,target_ast_sha256='d6c797957cd58e4b92514bcc10063e71045c1cdbe995aeeef3bff5020d434a11')
ARCHIVES=(LOG_ARCHIVE,TWO_ERROR_ARCHIVE,TERNARY_ARCHIVE,ARGUMENT_ARCHIVE,ORDER_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'logarithm':LOG_SOURCE,'two_error':TWO_ERROR_SOURCE,'inner_bound':INNER_SOURCE,
    'positive_natural':ARGUMENT_ENDPOINTS['positive_natural'],'drop_margin':ARGUMENT_HELPERS['drop_margin'],
    'le_gap':ORDER_HELPERS['le_gap'],'cancel_order':ORDER_HELPERS['cancel_order'],
    'power_nonzero':'forall a. ~a=0 -> forall k p. Pow(a,k,p) -> ~p=0',
    'succ_nonzero':'forall a. ~S a=0','mul_nonzero':'forall a b. ~a=0 -> ~b=0 -> ~(a*b)=0',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'mul_right_mono':'forall a b c. Le(a,b) -> Le(a*c,b*c)',
    'add_left_mono':'forall a b c. Le(a,b) -> Le(c+a,c+b)',
    'add_right_mono':'forall a b c. Le(a,b) -> Le(a+c,b+c)',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)','mul_comm':'forall a b. a*b=b*a',
    'mul_add':'forall a b c. a*(b+c)=a*b+a*c','add_mul':'forall a b c. (a+b)*c=a*c+b*c',
    'add_succ_left':'forall a b. S a+b=S(a+b)',
    'mul_le_cancel':'forall c a b. ~c=0 -> Le(c*a,c*b) -> Le(a,b)'}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(logarithm='CV093',two_error='CV101',inner_bound='CV086',positive_natural='AP006',drop_margin='AP006',
    le_gap='AP007',cancel_order='AP007',power_nonzero='AP006')
HELPER_DEPENDENCIES={'arithmetic':('mul_left_mono','mul_right_mono','add_left_mono','add_right_mono','le_trans','mul_assoc','mul_comm','mul_add','mul_le_cancel'),
    'AP082':('logarithm','two_error','inner_bound','positive_natural','drop_margin','le_gap','cancel_order','power_nonzero',
        'succ_nonzero','mul_nonzero','mul_assoc','mul_comm','add_mul','add_succ_left','arithmetic')}


class LogExpRefinementError(ValueError):
    """Changed actual log/exp data, finite horizons or either error allowance."""


def definition_registry():
    pool=dict(argument_registry())
    for name,spec in exp_registry().items():
        if name in pool:
            # Le/Lt have historical display-category differences only. Keep
            # the existing descriptor and compare every mathematical field.
            identity=('stable_id','name','parameters','template_source','template_formula','conceptual_dependencies')
            if any(getattr(pool[name],key)!=getattr(spec,key) for key in identity):
                raise LogExpRefinementError('log/exp shared conservative definition changed')
        else:pool[name]=spec
    result={};visiting=set()
    def visit(name):
        if name in result:return
        if name in visiting or name not in pool:raise LogExpRefinementError('missing or cyclic log/exp definition')
        visiting.add(name);spec=pool[name]
        for dep in spec.conceptual_dependencies:visit(dep)
        if spec.stable_id in {s.stable_id for s in result.values()}:raise LogExpRefinementError('duplicate log/exp definition identity')
        result[name]=spec;visiting.remove(name)
    for name in ('Le','NatAtanhPrefix','NatHornerValue','Pow','NatScaledExpRecurrence','Sum','IRatLe'):visit(name)
    return MappingProxyType(result)


def frozen_log_exp_refinement_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=23 or len(premises)!=15 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise LogExpRefinementError('AP082 exact supplied log/exp refinement target changed')
    return target


def source_contract():
    return dict(code='AP082',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=15,both_actual_logarithm_and_exponential_computations_preserved=True,
        independent_coefficient_scales_codes_and_exp_heads_allowed=True,
        coarse_log_length='M=k+1',fine_log_length='M+l',coarse_exp_degree='m',fine_exp_degree='m+1+N',
        logarithm_and_exponential_cutoffs_independent=True,all_three_actual_powers_preserved_and_nonzero=True,
        actual_ordered_log_gap_constructed=True,both_argument_denominators_proved_nonzero=True,
        positive_coefficient_factor_cancelled_only_after_proof=True,
        monotone_cross_value='b0*u<=a0*v',finite_error='27/p+2/P',
        zero_heads_k_l_m_and_N_allowed=True,rational_reading_requires_positive_heads=True,
        new_induction_needed=False,new_induction_count=0,new_definition_ids=[],definition_admissions=0,
        analytic_log_exp_identity_claimed=False,analytic_limit_claimed=False,fixed_approximation_program_changed=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def log_exp_refinement_source_pins():
    result=argument_modulus_source_pins()
    for source in (exp_two_error_bound_source_pins,exp_two_sided_continuity_source_pins):
        for name,pin in source().items():
            if name in result and result[name]!=pin:raise LogExpRefinementError('log/exp dependency source disagreement')
            result[name]=pin
    expected={'scripts/sqrt2_power_argument_modulus.py':'e8b4b0f02084fa368f60fcb69c6f265e15bb2cb7d35b16118c69cea174f2a451',
        'scripts/sqrt2_power_exp_two_error_bound.py':'df3b14dbae9c98536321540ac43a1fd804550da8bb8a26a5bb0664f2a24e92d1',
        'scripts/sqrt2_power_exp_two_sided_continuity.py':'8fd98e4b6733be1271387cf515dbf88ed4fabd48603a1169bd712b5385291086',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in ('scripts/sqrt2_power_argument_modulus.py','scripts/sqrt2_power_independent_atanh_truncation.py',
                 'scripts/sqrt2_power_ternary_atanh_bound.py','scripts/sqrt2_power_ternary_prefix_bound.py',
                 'scripts/sqrt2_power_exp_two_error_bound.py',
                 'scripts/sqrt2_power_exp_two_sided_continuity.py','scripts/sqrt2_power_quadratic_trace_exists.py',
                 'scripts/sqrt2_power_convolution_unit.py','scripts/sqrt2_power_finite_power_evaluation.py',
                 'scripts/sqrt2_power_quadratic_height.py','scripts/sqrt2_power_mixed_assembly.py'):
        if name not in result:raise LogExpRefinementError('unbound log/exp imported source: '+name)
    for name in (*expected,'scripts/sqrt2_power_log_exp_refinement.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:raise LogExpRefinementError('log/exp source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,parse_term
    two,three,nine=map(parse_term,('2','3','9'))
    def finish(t):
        F,p,P,g,a,b,u,v=t.terms(('F','p','P','g','a','b','u','v'))
        av,bu,ab=Mul(a,v),Mul(b,u),Mul(a,b);scale=Mul(p,F)
        left,base=Mul(scale,Mul(P,av)),Mul(scale,Mul(P,bu));other=Mul(two,scale)
        old=Mul(nine,Mul(g,P));new=Mul(nine,Mul(Mul(three,F),P))
        bound=apply(specialize(t,'mul_right_mono',g,Mul(three,F),P),t.hyp('gap_bound'))
        bound=apply(specialize(t,'mul_left_mono',Mul(g,P),Mul(Mul(three,F),P),nine),bound)
        bound=apply(specialize(t,'add_right_mono',old,new,other),bound)
        bound=apply(specialize(t,'mul_right_mono',Add(old,other),Add(new,other),ab),bound)
        bound=apply(specialize(t,'add_left_mono',Mul(Add(old,other),ab),Mul(Add(new,other),ab),base),bound)
        result=apply(specialize(t,'le_trans',left,Add(base,Mul(Add(old,other),ab)),Add(base,Mul(Add(new,other),ab))),t.hyp('error'),bound)
        A=Mul(Mul(nine,three),P);B=Mul(two,p);coefficient=Add(A,B)
        inner=_chain(CongAdd(_multiplicative_equal(t,new,Mul(F,A)),_multiplicative_equal(t,other,Mul(F,B))),
            EqSym(specialize(t,'mul_add',F,A,B)))
        err=_chain(CongMul(inner,EqRefl(ab)),specialize(t,'mul_assoc',F,coefficient,ab))
        X,Y=Mul(Mul(p,P),av),Mul(Mul(p,P),bu);E=Mul(coefficient,ab)
        rhs=_chain(CongAdd(_multiplicative_equal(t,base,Mul(F,Y)),err),EqSym(specialize(t,'mul_add',F,Y,E)))
        result=_left(t,registry,result,Add(base,Mul(Add(new,other),ab)),_multiplicative_equal(t,left,Mul(F,X)))
        result=_right(t,registry,result,Mul(F,X),rhs)
        return apply(specialize(t,'mul_le_cancel',F,X,Add(Y,E)),t.hyp('nonzero'),result)
    return introduce(s,('F','p','P','g','a','b','u','v'),('nonzero','gap_bound','error'),finish)


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import CongAdd,EqRefl
    from peano_lab.kernel.terms import Add,Mul,Succ,parse_term
    two,three=map(parse_term,('2','3'))
    def log_bounds(t):
        d,e,ab,ac,bb,bc,k,l,x,z,p,q=t.terms(PARAMETERS[:12])
        return apply(specialize(t,'logarithm',d,e,ab,ac,bb,bc,Succ(k),l,x,z,p,q),
            *(t.hyp(name) for name in ('nonzero_d','nonzero_e','log_coarse','log_fine','value_coarse','value_fine','power_p','power_q')))
    def chosen(t):
        d,e,ab,ac,bb,bc,k,l,x,z,p,q,m,N,cb,cc,eb,ec,a,b,u,v,P,g=t.terms(PARAMETERS+('g',))
        dp,eq=Mul(d,p),Mul(e,q);F=Mul(d,eq);X,Z=Mul(three,x),Mul(three,z);margin=Mul(three,d)
        power=lambda base,exponent,value,label:apply(instantiate(apply(specialize(t,'power_nonzero',base),specialize(t,'succ_nonzero',base.term)),exponent,value),t.hyp(label))
        pNZ=power(three,Succ(k),p,'power_p');qNZ=power(three,Add(Succ(k),l),q,'power_q');PNZ=power(two,m,P,'power_P')
        dpNZ=apply(specialize(t,'mul_nonzero',d,p),t.hyp('nonzero_d'),pNZ)
        eqNZ=apply(specialize(t,'mul_nonzero',e,q),t.hyp('nonzero_e'),qNZ)
        FNZ=apply(specialize(t,'mul_nonzero',d,eq),t.hyp('nonzero_d'),eqNZ)
        upper=apply(specialize(t,'positive_natural',Z,Add(X,margin),eq,dp),field(log_bounds(t),1,2))
        upper=_left(t,registry,upper,Mul(Add(X,margin),eq),specialize(t,'mul_comm',Z,dp))
        exact=_chain(specialize(t,'add_mul',X,margin,eq),CongAdd(specialize(t,'mul_comm',X,eq),specialize(t,'mul_assoc',three,d,eq)))
        upper=_right(t,registry,upper,Mul(dp,Z),exact)
        upper=_subst(t,registry,'Le(slot,(e*q)*(3*x)+3*(d*(e*q)))',t.hyp('gap'),upper)
        gap_bound=apply(specialize(t,'cancel_order',Mul(eq,X),g,Mul(three,F)),upper)
        length=specialize(t,'add_succ_left',k,l)
        fine_log=_subst(t,registry,'NatAtanhPrefix(e,bb,bc,slot)',length,t.hyp('log_fine'))
        fine_value=_subst(t,registry,'NatHornerValue(bb,bc,3,slot,z)',length,t.hyp('value_fine'))
        fine_power=_subst(t,registry,'Pow(3,slot,q)',length,t.hyp('power_q'))
        fine_range=apply(specialize(t,'inner_bound',e,bb,bc,Add(k,l),z,q),fine_log,fine_value,fine_power)
        fine_range=apply(specialize(t,'drop_margin',Z,Mul(three,e),eq),fine_range)
        estimate=apply(specialize(t,'two_error',dp,eq,X,Z,g,m,N,cb,cc,eb,ec,a,b,u,v,P),dpNZ,eqNZ,t.hyp('gap'),fine_range,
            *(t.hyp(name) for name in ('exp_coarse','exp_fine','head_coarse','head_fine','sum_coarse','sum_fine','power_P')))
        error=_subst(t,registry,'Le(slot*(P*(a0*v)),slot*(P*(b0*u))+(9*(g*P)+2*slot)*(a0*b0))',
            _multiplicative_equal(t,Mul(dp,eq),Mul(p,F)),field(estimate,1,2))
        error=apply(specialize(t,'arithmetic',F,p,P,g,a,b,u,v),FNZ,gap_bound,error)
        return conjunction(pNZ,qNZ,PNZ,dpNZ,eqNZ,field(estimate,0,2),error)
    def start(t):
        d,e,x,z,p,q=t.terms(('d','e','x','z','p','q'));dp,eq=Mul(d,p),Mul(e,q);X,Z=Mul(three,x),Mul(three,z)
        lower=apply(specialize(t,'positive_natural',X,Z,dp,eq),field(log_bounds(t),0,2))
        lower=_left(t,registry,lower,Mul(Z,dp),specialize(t,'mul_comm',X,eq))
        lower=_right(t,registry,lower,Mul(eq,X),specialize(t,'mul_comm',Z,dp))
        return eliminate(t,apply(specialize(t,'le_gap',Mul(eq,X),Mul(dp,Z)),lower),('g',),'gap',chosen)
    return introduce(s,PARAMETERS,('nonzero_d','nonzero_e','log_coarse','log_fine','value_coarse','value_fine','power_p','power_q',
        'exp_coarse','exp_fine','head_coarse','head_fine','sum_coarse','sum_fine','power_P'),start)


def prove_log_exp_refinement(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP082',target=frozen_log_exp_refinement_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'arithmetic':lambda s:_arithmetic(s,registry),'AP082':lambda s:_root(s,registry)},pins=log_exp_refinement_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
