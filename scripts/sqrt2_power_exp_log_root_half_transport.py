"""AP094: transport the actual original sample to the half-root exponential.

Preserve every original finite computation witness and its k+2 degree.
An independently normalized supplied exponential recurrence at the half-root
argument is no larger, and differs by at most 18/d. Only separately proved
nonzero factors are cancelled. No analytic identity or limit is assumed.
"""
from hashlib import sha256

from sqrt2_power_log_root_half_argument import (
    ROOT,Scope,introduce,apply,specialize,conjunction,field,canonical,json_hash,_and,
    log_root_half_argument_source_pins,NAMED_SOURCE as ARGUMENT_SOURCE,PARAMETERS as ARGUMENT_PARAMETERS,U,V,W,Z,
)
from sqrt2_power_supplied_exp_sample import (
    definition_registry,PARAMETERS as ORIGINAL_PARAMETERS,GRAPH as ORIGINAL_GRAPH,NAMED_SOURCE as SUPPLIED_SOURCE,
)
from sqrt2_power_exp_sample_modulus import exp_sample_modulus_source_pins,HORIZON_ARCHIVE,SUPPLIED_ARCHIVE
from sqrt2_power_exp_two_sided_continuity import NAMED_SOURCE as CONTINUITY_SOURCE,_left,_right
from sqrt2_power_exp_two_sided_horizons import CONTINUITY_ARCHIVE
from sqrt2_power_fixed_precision_threshold import _ground_equal,fixed_precision_threshold_source_pins
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-log-root-half-transport-v1'
PARAMETERS=ORIGINAL_PARAMETERS+('jb','jc','v','z')
PREMISES=('~D=0',ORIGINAL_GRAPH,'~v=0',f'NatScaledExpRecurrence({Z},{W},jb,jc,k+2)',
    'BetaAt(jb,jc,0,v)','Sum(jb,jc,S(k+2),z)')
PARTS=('~d=0',f'~{V}=0',f'~{Z}=0','~w0=0','~v=0','Le(w0*z,v*y)',
    'Le(d*(v*y),d*(w0*z)+18*(w0*v))')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> '+_and(PARTS)
TARGET_SHA256='d987799164353f66ab8981951790a46ec16203c12f377c44a23181eb042ebe7a'
ARITHMETIC_PARAMETERS=('d','V','Z','a','b','u','v')
ARITHMETIC_PREMISES=('~d=0','~V=0','~Z=0',
    'Le(d*((V*Z)*(a*v)),d*((V*Z)*(b*u))+9*(0*(a*b)))',
    'Le(d*((V*Z)*(b*u)),d*((V*Z)*(a*v))+9*((2*(V*Z))*(a*b)))')
HELPER_SOURCES={'eighteen':'9*2=18',
    'arithmetic':'forall '+' '.join(ARITHMETIC_PARAMETERS)+'. '+' -> '.join(ARITHMETIC_PREMISES)+
        ' -> Le(a*v,b*u) /\\ Le(d*(b*u),d*(a*v)+18*(a*b))'}
HELPER_TARGET_SHA256={'eighteen':'d4544aecef621221cfb4b033635aff0e67865296c467f137536dc54552fe20f6',
    'arithmetic':'1c6de1ecaa93a21e3bd0c80bf3400d7c0679a5039147936cc34d4cbed9f1b62b'}
ARGUMENT_ARCHIVE=dict(case='AP093',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-log-root-half-argument-v1/generation-process.json.gz',
    bytes=36913,sha256='15c7c978a377926e198298560ce910c7189c5e4ece5d4a9badb5e613aea4c041',
    raw_bytes=373435,raw_sha256='23a0b21ba851117bd70e070eb0237663341ed80f05680af0f07439c488bf0cf4',
    bundle_bytes=189044,bundle_sha256='d8a884f082830521daf08ad2866919f91894adbf5dcff76af374cdc6049f2ec5',
    nodes=69,root=68,target_ast_sha256='244e83e9bb6930441b55dd6bc755802920abede937100ccbd61c180210112cf3')
ARCHIVES=(ARGUMENT_ARCHIVE,CONTINUITY_ARCHIVE,HORIZON_ARCHIVE,SUPPLIED_ARCHIVE)
ENDPOINT_SOURCES={
    'arguments':ARGUMENT_SOURCE,'supplied':SUPPLIED_SOURCE,'continuity':CONTINUITY_SOURCE,
    'mul_ne_zero':'forall a b. ~a=0 -> ~b=0 -> ~(a*b)=0',
    'mul_le_cancel':'forall c a b. ~c=0 -> Le(c*a,c*b) -> Le(a,b)',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)','mul_comm':'forall a b. a*b=b*a',
    'mul_add':'forall a b c. a*(b+c)=a*b+a*c',
}
ENDPOINT_OWNERS={name:'AP008' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(arguments='AP093',supplied='AP004',continuity='AP007',mul_ne_zero='AP093')
HELPER_DEPENDENCIES={'eighteen':(),
    'arithmetic':('eighteen','mul_ne_zero','mul_le_cancel','mul_assoc','mul_comm','mul_add'),
    'AP094':('arguments','supplied','continuity','mul_left_mono','arithmetic')}


class ExpLogRootHalfTransportError(ValueError):
    """Changed original sample, independent head, finite degree or residual."""


def frozen_exp_log_root_half_transport_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    n,premises,out=strip_target(target)
    if n!=20 or len(premises)!=6 or type(out) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpLogRootHalfTransportError('AP094 exact original sample transport changed')
    return target


def source_contract():
    return dict(code='AP094',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=6,original_computation_graph_preserved=True,original_approximation_program_changed=False,
        original_degree='k+2',same_degree_on_both_actual_tables=True,original_prefix_length='2*k+1',
        second_argument_numerator=W,second_argument_denominator=Z,independent_positive_heads=True,
        output_order='z/v<=y/w0',finite_rational_error='0<=y/w0-z/v<=18/d',
        only_separately_proved_nonzero_factors_cancelled=True,new_definition_ids=[],definition_admissions=0,
        new_induction_count=0,new_induction_needed=False,tiny_ground_evaluator_max_value=32,
        new_solver_arithmetic_leaf='AP094-arithmetic',solver_hints_are_proof_authority=False,
        analytic_identity_claimed=False,analytic_limit_claimed=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_log_root_half_transport_source_pins():
    result=log_root_half_argument_source_pins()
    for source in (exp_sample_modulus_source_pins(),fixed_precision_threshold_source_pins()):
        for name,pin in source.items():
            if name in result and result[name]!=pin:raise ExpLogRootHalfTransportError('inherited proof source disagreement')
            result[name]=pin
    expected={pin['path']:dict(bytes=pin['bytes'],sha256=pin['sha256']) for pin in ARCHIVES}
    for name in ('scripts/sqrt2_power_supplied_exp_sample.py','scripts/sqrt2_power_exp_two_sided_continuity.py',
            'scripts/sqrt2_power_exp_two_sided_horizons.py','scripts/sqrt2_power_fixed_precision_threshold.py',
            'scripts/sqrt2_power_finite_power_evaluation.py','scripts/sqrt2_power_quadratic_height.py',
            'scripts/sqrt2_power_mixed_assembly.py'):
        if name not in result:raise ExpLogRootHalfTransportError('unbound imported constructor: '+name)
    for name in (*expected,'scripts/sqrt2_power_exp_log_root_half_transport.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        pin=dict(bytes=len(raw),sha256=sha256(raw).hexdigest())
        if len(raw)>2*1024**2 or name in expected and pin!=expected[name]:
            raise ExpLogRootHalfTransportError('transport source or actual archive changed')
        result[name]=pin
    return result


def _eighteen(s):
    from peano_lab.kernel.terms import parse_term
    return _ground_equal(parse_term('9*2'),parse_term('18'))


def _arithmetic(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,parse_term
    def finish(t):
        d,V,Z,a,b,u,v=t.terms(ARITHMETIC_PARAMETERS);zero,two,nine,eighteen=map(parse_term,('0','2','9','18'))
        Q=Mul(V,Z);DQ=Mul(d,Q);av=Mul(a,v);bu=Mul(b,u);ab=Mul(a,b)
        Qnz=apply(specialize(t,'mul_ne_zero',V,Z),t.hyp('V_nonzero'),t.hyp('Z_nonzero'))
        DQnz=apply(specialize(t,'mul_ne_zero',d,Q),t.hyp('d_nonzero'),Qnz)
        zproduct=_chain(specialize(t,'mul_comm',zero,ab),instantiate(Axiom('PA5'),ab))
        zerror=_chain(CongMul(EqRefl(nine),zproduct),instantiate(Axiom('PA5'),nine))
        clean=_chain(CongAdd(EqRefl(Mul(d,Mul(Q,bu))),zerror),instantiate(Axiom('PA3'),Mul(d,Mul(Q,bu))))
        lower=_right(t,registry,t.hyp('lower'),Mul(d,Mul(Q,av)),clean)
        lower=_left(t,registry,lower,Mul(d,Mul(Q,bu)),EqSym(specialize(t,'mul_assoc',d,Q,av)))
        lower=_right(t,registry,lower,Mul(DQ,av),EqSym(specialize(t,'mul_assoc',d,Q,bu)))
        lower=apply(specialize(t,'mul_le_cancel',DQ,av,bu),DQnz,lower)
        error=Mul(nine,Mul(Mul(two,Q),ab));end=Add(Mul(d,av),Mul(eighteen,ab))
        bound=_left(t,registry,t.hyp('upper'),Add(Mul(d,Mul(Q,av)),error),
            _multiplicative_equal(t,Mul(d,Mul(Q,bu)),Mul(Q,Mul(d,bu))))
        error_equal=_chain(_multiplicative_equal(t,error,Mul(Q,Mul(Mul(nine,two),ab))),
            CongMul(EqRefl(Q),CongMul(t.hyp('eighteen'),EqRefl(ab))))
        factored=_chain(CongAdd(_multiplicative_equal(t,Mul(d,Mul(Q,av)),Mul(Q,Mul(d,av))),error_equal),
            EqSym(specialize(t,'mul_add',Q,Mul(d,av),Mul(eighteen,ab))))
        bound=_right(t,registry,bound,Mul(Q,Mul(d,bu)),factored)
        bound=apply(specialize(t,'mul_le_cancel',Q,Mul(d,bu),end),Qnz,bound)
        return conjunction(lower,bound)
    return introduce(s,ARITHMETIC_PARAMETERS,('d_nonzero','V_nonzero','Z_nonzero','lower','upper'),finish)


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,EqSym
    from peano_lab.kernel.terms import Add,Mul,parse_term
    def finish(t):
        k,d,root,D,ab,ac,x,p,wb,wc,tb,tc,w0,f,h,y,jb,jc,v,z=t.terms(PARAMETERS)
        zero,two,three=map(parse_term,('0','2','3'));degree=Add(k,two)
        U,V,W,Z=Mul(Mul(three,x),d),Mul(Mul(D,p),root),Mul(Mul(three,x),root),Mul(two,Mul(Mul(D,p),d))
        graph=t.hyp('original');args=apply(specialize(t,'arguments',*t.terms(ARGUMENT_PARAMETERS)),
            t.hyp('scale_nonzero'),field(graph,0,9))
        actual=apply(specialize(t,'supplied',*t.terms(ORIGINAL_PARAMETERS)),t.hyp('scale_nonzero'),graph)
        lower=apply(specialize(t,'mul_left_mono',Mul(V,W),Mul(Z,U),d),field(args,8,10))
        lower=_right(t,registry,lower,Mul(d,Mul(V,W)),EqSym(instantiate(Axiom('PA3'),Mul(d,Mul(Z,U)))))
        estimates=apply(specialize(t,'continuity',V,Z,U,W,d,zero,Mul(two,Mul(V,Z)),degree,
            tb,tc,jb,jc,w0,v,y,z),field(args,4,10),field(args,5,10),field(args,6,10),field(args,7,10),
            lower,field(args,9,10),field(actual,3,5),t.hyp('half_terms'),field(graph,4,9),
            t.hyp('half_head'),field(graph,8,9),t.hyp('half_sum'))
        clean=apply(specialize(t,'arithmetic',d,V,Z,w0,v,y,z),field(args,0,10),field(args,4,10),
            field(args,5,10),field(estimates,0,2),field(estimates,1,2))
        return conjunction(field(args,0,10),field(args,4,10),field(args,5,10),field(actual,0,5),
            t.hyp('half_positive'),field(clean,0,2),field(clean,1,2))
    return introduce(s,PARAMETERS,('scale_nonzero','original','half_positive','half_terms','half_head','half_sum'),finish)


def factories(registry):return {'eighteen':_eighteen,'arithmetic':lambda s:_arithmetic(s,registry),'AP094':lambda s:_root(s,registry)}


def prove_exp_log_root_half_transport(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP094',target=frozen_exp_log_root_half_transport_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories(registry),
        pins=exp_log_root_half_transport_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
