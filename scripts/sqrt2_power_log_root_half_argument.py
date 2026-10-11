"""AP093: compare the original log/root argument with its half-root form.

For supplied actual finite data with positive coefficient scale, retain the
original quotient U/V and compare it with W/Z. Both denominators are proved
nonzero, both arguments are in [0,1], and 0<=U/V-W/Z<=2/d. This is an explicit
finite residual, not an exact identity or a claim about an analytic limit.
"""
from hashlib import sha256

from sqrt2_power_log_root_argument import (
    ROOT,Scope,introduce,witness,apply,specialize,conjunction,field,canonical,json_hash,
    definition_registry,GRAPH,OUTPUTS,_and,BOUND_SOURCE,
)
from sqrt2_power_log_root_independence import log_root_independence_source_pins,ARGUMENT_ARCHIVE,SQUARE_ARCHIVE,SQUARE_SOURCE
from sqrt2_power_scaled_exp_tail import BOUND_ARCHIVE
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-log-root-half-argument-v1'
PARAMETERS=('k',)+OUTPUTS
# Display substitutions only; no new definition or function symbol.
U='((3*x)*d)';V='((D*p)*s)';W='((3*x)*s)';Z='(2*((D*p)*d))'
PARTS=('~d=0','~s=0','~p=0','~(D*p)=0',f'~{V}=0',f'~{Z}=0',
    f'Le({U},{V})',f'Le({W},{Z})',f'Le({V}*{W},{Z}*{U})',
    f'Le(d*({Z}*{U}),d*({V}*{W})+2*({V}*{Z}))')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. ~D=0 -> '+GRAPH+' -> '+_and(PARTS)
TARGET_SHA256='244e83e9bb6930441b55dd6bc755802920abede937100ccbd61c180210112cf3'
HELPER_PARTS=('~(B*s)=0','~(2*(B*d))=0','Le(A*d,B*s)','Le(A*s,2*(B*d))',
    'Le((B*s)*(A*s),(2*(B*d))*(A*d))',
    'Le(d*((2*(B*d))*(A*d)),d*((B*s)*(A*s))+2*((B*s)*(2*(B*d))))')
HELPER_PREMISES=('~B=0','~d=0','~s=0','Le(d,s)','Le(s,2*d)','Le(A,B)',
    'Le(s*s,2*(d*d))','Le(2*(d*d),s*s+2*(2*d))')
HELPER_SOURCES={'arithmetic':'forall A B d s. '+' -> '.join(HELPER_PREMISES)+' -> '+_and(HELPER_PARTS)}
HELPER_TARGET_SHA256={'arithmetic':'312add90eebbf75d44c4fd8aefbd7418034d9701b6f0bb65fde0f86df502377e'}
ARCHIVES=(ARGUMENT_ARCHIVE,SQUARE_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={
    'inner_bound':BOUND_SOURCE,'square':SQUARE_SOURCE,
    'power_nonzero':'forall a. ~a=0 -> forall k p. Pow(a,k,p) -> ~p=0',
    'succ_ne_zero':'forall a. ~S a=0','mul_ne_zero':'forall a b. ~a=0 -> ~b=0 -> ~(a*b)=0',
    'le_self_succ':'forall a. Le(a,S a)',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'mul_right_mono':'forall a b c. Le(a,b) -> Le(a*c,b*c)',
    'add_left_mono':'forall a b c. Le(a,b) -> Le(c+a,c+b)',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)','mul_comm':'forall a b. a*b=b*a',
    'mul_add':'forall a b c. a*(b+c)=a*b+a*c','add_comm':'forall a b. a+b=b+a',
}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(inner_bound='AP001',square='SQ009',power_nonzero='AP001',
    succ_ne_zero='AP001',mul_ne_zero='AP001',le_self_succ='SQ009')
HELPER_DEPENDENCIES={
    'arithmetic':('succ_ne_zero','mul_ne_zero','mul_left_mono','mul_right_mono','add_left_mono',
        'le_trans','mul_assoc','mul_comm','mul_add'),
    'AP093':('inner_bound','square','power_nonzero','succ_ne_zero','mul_ne_zero','le_self_succ',
        'le_trans','add_comm','arithmetic'),
}


class LogRootHalfArgumentError(ValueError):
    """Changed actual quotient, scale guard, residual, or ordinary dependency."""


def frozen_log_root_half_argument_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=8 or len(premises)!=2 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise LogRootHalfArgumentError('AP093 exact supplied original-argument comparison changed')
    return target


def source_contract():
    return dict(code='AP093',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=2,supplied_original_computation_preserved=True,positive_coefficient_scale_required=True,
        original_argument_numerator=U,original_argument_denominator=V,half_root_numerator=W,half_root_denominator=Z,
        both_denominators_nonzero_proved=True,both_arguments_in_unit_interval_proved=True,
        finite_rational_error='0<=U/V-W/Z<=2/d',finite_equality_claimed=False,
        all_precisions_including_zero=True,original_prefix_length='2*k+1',
        original_approximation_program_changed=False,new_definition_ids=[],definition_admissions=0,
        new_induction_count=0,new_induction_needed=False,new_solver_arithmetic_leaf='AP093-arithmetic',
        solver_hints_are_proof_authority=False,analytic_identity_claimed=False,analytic_limit_claimed=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def log_root_half_argument_source_pins():
    result=log_root_independence_source_pins()
    expected={pin['path']:dict(bytes=pin['bytes'],sha256=pin['sha256']) for pin in ARCHIVES}
    for name in ('scripts/sqrt2_power_finite_power_evaluation.py','scripts/sqrt2_power_quadratic_height.py',
            'scripts/sqrt2_power_convolution_unit.py','scripts/sqrt2_power_mixed_assembly.py',
            'scripts/sqrt2_power_scaled_exp_tail.py'):
        if name not in result:raise LogRootHalfArgumentError('unbound imported constructor: '+name)
    for name in (*expected,'scripts/sqrt2_power_log_root_half_argument.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        pin=dict(bytes=len(raw),sha256=sha256(raw).hexdigest())
        if len(raw)>2*1024**2 or name in expected and pin!=expected[name]:
            raise LogRootHalfArgumentError('half-root argument source or archive changed')
        result[name]=pin
    return result


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongAdd
    from peano_lab.kernel.terms import Add,Mul,parse_term,pretty_term
    def finish(t):
        A,B,d,root=t.terms(('A','B','d','s'));one,two=map(parse_term,('1','2'))
        U,V,W,Z=Mul(A,d),Mul(B,root),Mul(A,root),Mul(two,Mul(B,d))
        def left(proof,right,equality):
            return _subst(t,registry,'Le(slot,'+pretty_term(right,list(t.variables))+')',equality,proof)
        def right(proof,left_term,equality):
            return _subst(t,registry,'Le('+pretty_term(left_term,list(t.variables))+',slot)',equality,proof)
        Vnz=apply(specialize(t,'mul_ne_zero',B,root),t.hyp('B_nonzero'),t.hyp('s_nonzero'))
        Bdnz=apply(specialize(t,'mul_ne_zero',B,d),t.hyp('B_nonzero'),t.hyp('d_nonzero'))
        Znz=apply(specialize(t,'mul_ne_zero',two,Mul(B,d)),specialize(t,'succ_ne_zero',one),Bdnz)
        ad=apply(specialize(t,'mul_right_mono',A,B,d),t.hyp('log_bound'))
        bd=apply(specialize(t,'mul_left_mono',d,root,B),t.hyp('root_lower'))
        Ub=apply(specialize(t,'le_trans',U,Mul(B,d),V),ad,bd)
        ar=apply(specialize(t,'mul_right_mono',A,B,root),t.hyp('log_bound'))
        br=apply(specialize(t,'mul_left_mono',root,Mul(two,d),B),t.hyp('root_upper'))
        br=right(br,V,_multiplicative_equal(t,Mul(B,Mul(two,d)),Z))
        Wb=apply(specialize(t,'le_trans',W,V,Z),ar,br)
        factor=Mul(A,B);lo=Mul(V,W);hi=Mul(Z,U)
        lower=apply(specialize(t,'mul_left_mono',Mul(root,root),Mul(two,Mul(d,d)),factor),t.hyp('square_lower'))
        lower=left(lower,Mul(factor,Mul(two,Mul(d,d))),_multiplicative_equal(t,Mul(factor,Mul(root,root)),lo))
        lower=right(lower,lo,_multiplicative_equal(t,Mul(factor,Mul(two,Mul(d,d))),hi))
        factor=Mul(d,factor);a,b,c=Mul(two,Mul(d,d)),Mul(root,root),Mul(two,Mul(two,d))
        lhs,base,error=Mul(d,hi),Mul(d,lo),Mul(Mul(two,Z),U)
        upper=apply(specialize(t,'mul_left_mono',a,Add(b,c),factor),t.hyp('square_upper'))
        upper=left(upper,Mul(factor,Add(b,c)),_multiplicative_equal(t,Mul(factor,a),lhs))
        expanded=_chain(specialize(t,'mul_add',factor,b,c),
            CongAdd(_multiplicative_equal(t,Mul(factor,b),base),_multiplicative_equal(t,Mul(factor,c),error)))
        upper=right(upper,lhs,expanded)
        allowance=Mul(two,Mul(V,Z))
        error_bound=apply(specialize(t,'mul_left_mono',U,V,Mul(two,Z)),Ub)
        error_bound=right(error_bound,error,_multiplicative_equal(t,Mul(Mul(two,Z),V),allowance))
        enlarged=apply(specialize(t,'add_left_mono',error,allowance,base),error_bound)
        upper=apply(specialize(t,'le_trans',lhs,Add(base,error),Add(base,allowance)),upper,enlarged)
        return conjunction(Vnz,Znz,Ub,Wb,lower,upper)
    return introduce(s,('A','B','d','s'),('B_nonzero','d_nonzero','s_nonzero','root_lower','root_upper',
        'log_bound','square_lower','square_upper'),finish)


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.terms import Add,Mul,Succ,parse_term
    def finish(t):
        k,d,root,D,ab,ac,x,p=t.terms(PARAMETERS);two,three=map(parse_term,('2','3'))
        graph=t.hyp('graph');square=apply(specialize(t,'square',k,d,root),field(graph,0,4))
        pnz=apply(instantiate(apply(specialize(t,'power_nonzero',three),specialize(t,'succ_ne_zero',two)),Succ(Mul(two,k)),p),field(graph,3,4))
        B=Mul(D,p);A=Mul(three,x);margin=Mul(three,D)
        Bnz=apply(specialize(t,'mul_ne_zero',D,p),t.hyp('D_nonzero'),pnz)
        bound=apply(specialize(t,'inner_bound',D,ab,ac,Mul(two,k),x,p),*(field(graph,i,4) for i in (1,2,3)))
        drop=witness((margin,),specialize(t,'add_comm',margin,A))
        bound=apply(specialize(t,'le_trans',A,Add(A,margin),B),drop,bound)
        upper=apply(specialize(t,'le_trans',root,Succ(root),Mul(two,d)),specialize(t,'le_self_succ',root),field(square,3,6))
        result=apply(specialize(t,'arithmetic',A,B,d,root),Bnz,field(square,0,6),field(square,1,6),
            field(square,2,6),upper,bound,field(square,4,6),field(square,5,6))
        return conjunction(field(square,0,6),field(square,1,6),pnz,Bnz,*(field(result,i,6) for i in range(6)))
    return introduce(s,PARAMETERS,('D_nonzero','graph'),finish)


def factories(registry):return {'arithmetic':lambda s:_arithmetic(s,registry),'AP093':_root}


def prove_log_root_half_argument(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP093',target=frozen_log_root_half_argument_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories(registry),
        pins=log_root_half_argument_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
