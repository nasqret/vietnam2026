"""AP085: uniform near-two bounds for the fixed logarithm/exp index schedule.

For k>=18*r+2, construct the actual cutoff gap and align the supplied
logarithm length 2*k+1 and exponential degree k+2 with AP084. No computation
is changed, no code equality is assumed, and the root quotient is not claimed.
"""
from hashlib import sha256

from sqrt2_power_log_exp_uniform_two import (
    ROOT,Scope,introduce,eliminate,witness,apply,specialize,conjunction,field,canonical,json_hash,
    definition_registry,log_exp_uniform_two_source_pins,NAMED_SOURCE as UNIFORM_SOURCE,BOUND_ARCHIVE,
)
from sqrt2_power_log_exp_refinement import ORDER_ARCHIVE
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-fixed-log-exp-convergence-v1'
PARAMETERS=('k','d','ab','ac','x','p','tb','tc','h','y')
PREMISES=('Le(S(S(18*r)),k)','~d=0','NatAtanhPrefix(d,ab,ac,S(2*k))',
    'NatHornerValue(ab,ac,3,S(2*k),x)','Pow(3,S(2*k),p)',
    'NatScaledExpRecurrence(d*p,3*x,tb,tc,S(S k))','BetaAt(tb,tc,0,h)','Sum(tb,tc,S(S(S k)),y)')
CONCLUSION='~p=0 /\\ (~(d*p)=0 /\\ (Le(r*y,(r*2)*h+2*h) /\\ Le((r*2)*h,r*y+h)))'
LATER_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> '+CONCLUSION
NAMED_SOURCE='forall n. exists r. Pow(2,n,r) /\\ (~r=0 /\\ ('+LATER_SOURCE+'))'
TARGET_SHA256='c49cb9e52773c0bae1157f7b1eedbc0f29391c3163cb80a3c9c28445c69c37b1'
HELPER_SOURCES={'indices':'forall M t k. k=M+t -> S(2*k)=M+S(k+t) /\\ S(S k)=(S M)+(S t)'}
HELPER_TARGET_SHA256={'indices':'96382100568fbd357c8677f0cc92d16a6846aa7c11a301f1c0fc9345a1d2af31'}
UNIFORM_ARCHIVE=dict(case='AP084',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-log-exp-uniform-two-v2/generation-process.json.gz',
    bytes=205521,sha256='5d2b746cfb9e0d98d5b3b695cdf61e160ce02dc344fa243a813593514fb38f0e',
    raw_bytes=5404390,raw_sha256='47331a3a9269157304e2325ec169ff1b281f33912dbb7e77dedfa1e7a1f335fe',
    bundle_bytes=3313343,bundle_sha256='0bf21cd1c9bfc2162b766da7d48f010422e725cddc665f08f8d2b12460ef34ce',
    nodes=511,root=510,target_ast_sha256='018632b34699a2f0f8feb879b56eb195d89cfb1304ffe2f5da46ef3ed3607898')
ARCHIVES=(UNIFORM_ARCHIVE,ORDER_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'uniform':UNIFORM_SOURCE,'le_gap':'forall a b. Le(a,b) -> exists g. b=a+g',
    'add_assoc':'forall a b c. (a+b)+c=a+(b+c)','add_comm':'forall a b. a+b=b+a',
    'add_succ_left':'forall a b. S a+b=S(a+b)','mul_succ_left':'forall a b. (S a)*b=a*b+b',
    'one_mul':'forall a. 1*a=a'}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(uniform='AP084',le_gap='AP007')
HELPER_DEPENDENCIES={'indices':('add_assoc','add_comm','add_succ_left','mul_succ_left','one_mul'),
    'AP085':('uniform','le_gap','indices')}


class FixedLogExpConvergenceError(ValueError):
    """Changed actual fixed index schedule, cutoff or uniform error statement."""


def frozen_fixed_log_exp_convergence_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=1 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise FixedLogExpConvergenceError('AP085 exact fixed logarithm/exp schedule changed')
    return target


def source_contract():
    return dict(code='AP085',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,all_requested_precisions_including_zero=True,actual_precision_power='r=2^n',
        precision_chosen_before_all_later_computations=True,coefficient_scale_positive_required=True,
        supplied_computation_and_codes_preserved=True,fixed_logarithm_prefix_length='2*k+1',fixed_exp_degree='k+2',
        sufficient_threshold='18*r+2<=k',actual_cutoff_gap_constructed=True,
        logarithm_horizon_alignment='2*k+1=M+(k+t+1) when k=M+t',
        exponential_horizon_alignment='k+2=(M+1)+(t+1) when k=M+t',
        actual_power_and_argument_denominator_proved_nonzero=True,
        finite_upper_error='y/h<=2+2/r',finite_lower_error='2-1/r<=y/h',
        rational_reading_requires_positive_head=True,zero_head_allowed=True,
        AP020_log_interface_compatible_but_not_a_proof_dependency=True,
        root_quotient_accuracy_claimed=False,analytic_log_exp_identity_claimed=False,analytic_limit_claimed=False,
        fixed_approximation_program_changed=False,new_induction_count=0,new_induction_needed=False,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def fixed_log_exp_convergence_source_pins():
    result=log_exp_uniform_two_source_pins()
    expected={'scripts/sqrt2_power_log_exp_uniform_two.py':'470eee5a093ae4c0c089ee4652a7a474037ac8514ea30d4c42ff08e8bffa9227',
        'scripts/sqrt2_power_finite_odd_log_series.py':'df1df76ba27d8e0860f991f68a4d7790c7c758c600fca962ea24e6a5389d9c3b',
        'scripts/sqrt2_power_odd_horner_quotient.py':'2f646e44d68612e31791b15cc24e59c6c9d7ec47059e686a81a1a3fc963e7d0e',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in ('scripts/sqrt2_power_log_exp_refinement.py','scripts/sqrt2_power_convolution_unit.py',
                 'scripts/sqrt2_power_quadratic_height.py','scripts/sqrt2_power_mixed_assembly.py'):
        if name not in result:raise FixedLogExpConvergenceError('unbound fixed-index proof constructor: '+name)
    for name in (*expected,'scripts/sqrt2_power_fixed_log_exp_convergence.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:raise FixedLogExpConvergenceError('fixed-index source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _indices(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,CongS,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Succ,parse_term
    one=parse_term('1')
    def finish(t):
        M,j,k=t.terms(('M','t','k'))
        double=_chain(specialize(t,'mul_succ_left',one,k),CongAdd(specialize(t,'one_mul',k),EqRefl(k)))
        logarithm=_chain(CongS(double),CongS(CongAdd(t.hyp('gap'),EqRefl(k))),
            CongS(specialize(t,'add_assoc',M,j,k)),CongS(CongAdd(EqRefl(M),specialize(t,'add_comm',j,k))),
            EqSym(instantiate(Axiom('PA4'),M,Add(k,j))))
        expanded=_chain(instantiate(Axiom('PA4'),Succ(M),j),CongS(specialize(t,'add_succ_left',M,j)))
        exponential=_chain(CongS(CongS(t.hyp('gap'))),EqSym(expanded))
        return conjunction(logarithm,exponential)
    return introduce(s,('M','t','k'),('gap',),finish)


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import CongS
    from peano_lab.kernel.terms import Add,Mul,Succ,parse_term
    eighteen=parse_term('18')
    def chosen(t):
        r,k,d,ab,ac,x,p,tb,tc,h,y,j=t.terms(('r',)+PARAMETERS+('offset',))
        M=Succ(Succ(Mul(eighteen,r)));l=Succ(Add(k,j));N=Succ(j)
        lengths=apply(specialize(t,'indices',M,j,k),t.hyp('gap'));log=field(lengths,0,2);exp=field(lengths,1,2)
        prefix=_subst(t,registry,'NatAtanhPrefix(d,ab,ac,slot)',log,t.hyp('prefix'))
        value=_subst(t,registry,'NatHornerValue(ab,ac,3,slot,x)',log,t.hyp('value'))
        power=_subst(t,registry,'Pow(3,slot,p)',log,t.hyp('power'))
        terms=_subst(t,registry,'NatScaledExpRecurrence(d*p,3*x,tb,tc,slot)',exp,t.hyp('terms'))
        total=_subst(t,registry,'Sum(tb,tc,slot,y)',CongS(exp),t.hyp('total'))
        universal=field(t.hyp('uniform_data'),2,3)
        return apply(instantiate(universal,d,ab,ac,l,x,p,N,tb,tc,h,y),t.hyp('nonzero'),prefix,value,power,terms,t.hyp('head'),total)
    def later(t):
        M=Succ(Succ(Mul(eighteen,t.term('r'))))
        gap=apply(specialize(t,'le_gap',M,t.term('k')),t.hyp('threshold'))
        return eliminate(t,gap,('offset',),'gap',chosen)
    def precision(t):
        universal=introduce(t,PARAMETERS,('threshold','nonzero','prefix','value','power','terms','head','total'),later)
        return witness((t.term('r'),),conjunction(field(t.hyp('uniform_data'),0,3),field(t.hyp('uniform_data'),1,3),universal))
    return introduce(s,('n',),(),lambda t:eliminate(t,specialize(t,'uniform',t.term('n')),('r',),'uniform_data',precision))


def prove_fixed_log_exp_convergence(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP085',target=frozen_fixed_log_exp_convergence_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'indices':_indices,'AP085':lambda s:_root(s,registry)},pins=fixed_log_exp_convergence_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
