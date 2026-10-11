"""AP087: independent half-logarithm exponential refinement.

Keep the original logarithm tables and halve only the actual exponential
arguments, with explicitly doubled denominators and a proved scaled gap.
No claim that doubling a denominator preserves an atanh-prefix predicate.
"""
from hashlib import sha256

from sqrt2_power_log_exp_refinement import (
    ROOT,Scope,introduce,eliminate,apply,specialize,conjunction,field,canonical,json_hash,
    definition_registry,log_exp_refinement_source_pins,PARAMETERS,
    PREMISES as FULL_PREMISES,CONCLUSION as FULL_CONCLUSION,
    ENDPOINT_SOURCES as FULL_ENDPOINTS,ENDPOINT_OWNERS as FULL_OWNERS,
    HELPER_SOURCES as FULL_HELPERS,ARCHIVES as FULL_ARCHIVES,
    _left,_right,_subst,_multiplicative_equal,_chain,
)
from sqrt2_power_exp_two_sided_continuity import HELPER_SOURCES as ORDER_HELPERS
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-half-log-exp-refinement-v1'
PREMISES=tuple(p.replace('NatScaledExpRecurrence(d*p,','NatScaledExpRecurrence(2*(d*p),')
    .replace('NatScaledExpRecurrence(e*q,','NatScaledExpRecurrence(2*(e*q),') for p in FULL_PREMISES)
CONCLUSION=FULL_CONCLUSION.replace('~(d*p)=0','~(2*(d*p))=0').replace('~(e*q)=0','~(2*(e*q))=0')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> '+CONCLUSION
TARGET_SHA256='74d9571876bc3c082af4e6ab56b2f18a0e49718f24ef4ea8fe3ddf85f58dcf49'
HELPER_SOURCES={'scaled_gap':'forall d e x z g F. d*z=e*x+g -> Le(g,3*F) -> Le(z,e) -> (2*d)*z=(2*e)*x+2*g /\\ (Le(2*g,3*((2*2)*F)) /\\ Le(z,2*e))'}
HELPER_TARGET_SHA256={'scaled_gap':'2a1e3e8c59d810503c53737cdba754975d0b0758877c05e39115fb4ca90a4c3c'}
NORMALIZE_ARCHIVE=dict(case='AP082',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-log-exp-refinement-v1/generation-process.json.gz',
    bytes=83922,sha256='ef36aa0c4ccae3b2abbf9ddcd08879e41bfeae4722465e3a999722e153359b55',
    raw_bytes=1512006,raw_sha256='8fb69065eddf8392adc748921171e9fe7e03ff7b0bcaa6cf95fb62be3c2691bd',
    bundle_bytes=892431,bundle_sha256='0261db5cc15244a1345941dd847fc8bf283af92dbb74cf19ff6a9f22168eff88',
    nodes=229,root=228,target_ast_sha256='bccfdfa515c324f3b34a5a205185f1a81d590d8d27d1b41dcba91fbbd65883cc')
ARCHIVES=(*FULL_ARCHIVES,NORMALIZE_ARCHIVE)
ENDPOINT_SOURCES={**FULL_ENDPOINTS,'normalize':FULL_HELPERS['arithmetic'],'bound_two':ORDER_HELPERS['bound_two']}
ENDPOINT_OWNERS={**FULL_OWNERS,'normalize':'AP082','bound_two':'AP007'}
HELPER_DEPENDENCIES={'scaled_gap':('mul_assoc','mul_comm','mul_add','mul_left_mono','bound_two'),
    'AP087':('logarithm','two_error','inner_bound','positive_natural','drop_margin','le_gap','cancel_order','power_nonzero',
        'succ_nonzero','mul_nonzero','mul_assoc','mul_comm','add_mul','add_succ_left','normalize','scaled_gap')}


class HalfLogExpRefinementError(ValueError):
    """Changed original logarithm data, half argument or either error budget."""


def frozen_half_log_exp_refinement_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=23 or len(premises)!=15 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise HalfLogExpRefinementError('AP087 exact supplied half-logarithm refinement changed')
    return target


def source_contract():
    return dict(code='AP087',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=15,both_actual_logarithm_and_exponential_computations_preserved=True,
        original_logarithm_prefix_and_horner_scales_unchanged=True,
        exponential_arguments_explicitly_halved=True,half_arguments=['3*x/(2*d*p)','3*z/(2*e*q)'],
        independent_coefficient_scales_codes_and_exp_heads_allowed=True,
        coarse_log_length='M=k+1',fine_log_length='M+l',coarse_exp_degree='m',fine_exp_degree='m+1+N',
        logarithm_and_exponential_cutoffs_independent=True,actual_ordered_log_gap_constructed=True,
        doubled_argument_denominators_proved_nonzero=True,positive_factor='(2*2)*(d*(e*q))',
        positive_coefficient_factor_cancelled_only_after_proof=True,
        monotone_cross_value='b0*u<=a0*v',finite_error='27/p+2/P',error_not_claimed_sharp=True,
        zero_heads_k_l_m_and_N_allowed=True,rational_reading_requires_positive_heads=True,
        new_induction_needed=False,new_induction_count=0,new_definition_ids=[],definition_admissions=0,
        analytic_log_exp_identity_claimed=False,analytic_limit_claimed=False,sqrt2_identification_claimed=False,
        fixed_approximation_program_changed=False,original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def half_log_exp_refinement_source_pins():
    result=log_exp_refinement_source_pins()
    expected={'scripts/sqrt2_power_log_exp_refinement.py':'51d0cc8fecf2f4289ac4da3da4a21c660939dac4760580b8372443f861d3b104',
        NORMALIZE_ARCHIVE['path']:NORMALIZE_ARCHIVE['sha256']}
    for name in (*expected,'scripts/sqrt2_power_half_log_exp_refinement.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise HalfLogExpRefinementError('half-log refinement source or archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _scaled_gap(s,registry):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,parse_term
    two,three=map(parse_term,('2','3'))
    def finish(t):
        d,e,x,z,g,F=t.terms(('d','e','x','z','g','F'))
        ex,tg=Mul(e,x),Mul(two,g)
        gap=_chain(specialize(t,'mul_assoc',two,d,z),CongMul(EqRefl(two),t.hyp('gap')),
            specialize(t,'mul_add',two,ex,g),CongAdd(EqSym(specialize(t,'mul_assoc',two,e,x)),EqRefl(tg)))
        enlarged=Mul(two,Mul(three,F));twice=Mul(two,enlarged);factor=Mul(Mul(two,two),F)
        bound=apply(specialize(t,'mul_left_mono',g,Mul(three,F),two),t.hyp('error'))
        bound=apply(specialize(t,'bound_two',tg,enlarged),bound)
        bound=_right(t,registry,bound,tg,_multiplicative_equal(t,twice,Mul(three,factor)))
        return conjunction(gap,bound,apply(specialize(t,'bound_two',z,e),t.hyp('range')))
    return introduce(s,('d','e','x','z','g','F'),('gap','error','range'),finish)


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import CongAdd,EqRefl
    from peano_lab.kernel.terms import Add,Mul,Succ,parse_term
    one,two,three=map(parse_term,('1','2','3'))
    def log_bounds(t):
        d,e,ab,ac,bb,bc,k,l,x,z,p,q=t.terms(PARAMETERS[:12])
        return apply(specialize(t,'logarithm',d,e,ab,ac,bb,bc,Succ(k),l,x,z,p,q),
            *(t.hyp(name) for name in ('nonzero_d','nonzero_e','log_coarse','log_fine','value_coarse','value_fine','power_p','power_q')))
    def chosen(t):
        d,e,ab,ac,bb,bc,k,l,x,z,p,q,m,N,cb,cc,eb,ec,a,b,u,v,P,g=t.terms(PARAMETERS+('g',))
        dp,eq=Mul(d,p),Mul(e,q);F=Mul(d,eq);X,Z=Mul(three,x),Mul(three,z);margin=Mul(three,d)
        D,E=Mul(two,dp),Mul(two,eq);scaledF=Mul(Mul(two,two),F);scaledg=Mul(two,g)
        power=lambda base,exponent,value,label:apply(instantiate(apply(specialize(t,'power_nonzero',base),specialize(t,'succ_nonzero',base.term)),exponent,value),t.hyp(label))
        pNZ=power(three,Succ(k),p,'power_p');qNZ=power(three,Add(Succ(k),l),q,'power_q');PNZ=power(two,m,P,'power_P')
        dpNZ=apply(specialize(t,'mul_nonzero',d,p),t.hyp('nonzero_d'),pNZ)
        eqNZ=apply(specialize(t,'mul_nonzero',e,q),t.hyp('nonzero_e'),qNZ)
        twoNZ=specialize(t,'succ_nonzero',one)
        DNZ=apply(specialize(t,'mul_nonzero',two,dp),twoNZ,dpNZ)
        ENZ=apply(specialize(t,'mul_nonzero',two,eq),twoNZ,eqNZ)
        FNZ=apply(specialize(t,'mul_nonzero',d,eq),t.hyp('nonzero_d'),eqNZ)
        fourNZ=apply(specialize(t,'mul_nonzero',two,two),twoNZ,twoNZ)
        scaledFNZ=apply(specialize(t,'mul_nonzero',Mul(two,two),F),fourNZ,FNZ)
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
        scaled=apply(specialize(t,'scaled_gap',dp,eq,X,Z,g,F),t.hyp('gap'),gap_bound,fine_range)
        estimate=apply(specialize(t,'two_error',D,E,X,Z,scaledg,m,N,cb,cc,eb,ec,a,b,u,v,P),DNZ,ENZ,field(scaled,0,3),field(scaled,2,3),
            *(t.hyp(name) for name in ('exp_coarse','exp_fine','head_coarse','head_fine','sum_coarse','sum_fine','power_P')))
        error=_subst(t,registry,'Le(slot*(P*(a0*v)),slot*(P*(b0*u))+(9*((2*g)*P)+2*slot)*(a0*b0))',
            _multiplicative_equal(t,Mul(D,E),Mul(p,scaledF)),field(estimate,1,2))
        error=apply(specialize(t,'normalize',scaledF,p,P,scaledg,a,b,u,v),scaledFNZ,field(scaled,1,3),error)
        return conjunction(pNZ,qNZ,PNZ,DNZ,ENZ,field(estimate,0,2),error)
    def start(t):
        d,e,x,z,p,q=t.terms(('d','e','x','z','p','q'));dp,eq=Mul(d,p),Mul(e,q);X,Z=Mul(three,x),Mul(three,z)
        lower=apply(specialize(t,'positive_natural',X,Z,dp,eq),field(log_bounds(t),0,2))
        lower=_left(t,registry,lower,Mul(Z,dp),specialize(t,'mul_comm',X,eq))
        lower=_right(t,registry,lower,Mul(eq,X),specialize(t,'mul_comm',Z,dp))
        return eliminate(t,apply(specialize(t,'le_gap',Mul(eq,X),Mul(dp,Z)),lower),('g',),'gap',chosen)
    return introduce(s,PARAMETERS,('nonzero_d','nonzero_e','log_coarse','log_fine','value_coarse','value_fine','power_p','power_q',
        'exp_coarse','exp_fine','head_coarse','head_fine','sum_coarse','sum_fine','power_P'),start)


def prove_half_log_exp_refinement(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP087',target=frozen_half_log_exp_refinement_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'scaled_gap':lambda s:_scaled_gap(s,registry),'AP087':lambda s:_root(s,registry)},pins=half_log_exp_refinement_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
