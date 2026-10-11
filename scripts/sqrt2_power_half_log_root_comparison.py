"""AP049: compare a half-log square witness with a dyadic root witness.

This is natural arithmetic on supplied finite bounds. If r<=d, the square
errors 3/r and 4/d imply a forward error 7/r; the reverse error is 1/r.
Only positive h*d is cancelled. Actual witnesses are a separate construction.
"""
from hashlib import sha256

from sqrt2_power_square_error_linear import (
    ROOT,Scope,introduce,witness,apply,specialize,conjunction,canonical,json_hash,
    definition_registry,square_error_linear_source_pins,NAMED_SOURCE as LINEAR_SOURCE,BOUND_ARCHIVE,
)
from sqrt2_power_exp_two_sided_continuity import _left,_right
from sqrt2_power_quadratic_height import _chain,_additive_equal
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-half-log-root-comparison-v1'
PARAMETERS=('r','u','h','s','d')
ROOT_LOWER='Le(s*s,2*(d*d))'
ROOT_UPPER='Le(2*(d*d),s*s+2*(2*d))'
HALF_UPPER='Le(r*(u*u),(r*2)*(h*h)+3*(h*h))'
HALF_LOWER='Le((r*2)*(h*h),r*(u*u)+(h*h))'
PREMISES=('~h=0','~d=0','Le(r,d)','Le(d,s)',ROOT_LOWER,ROOT_UPPER,HALF_UPPER,HALF_LOWER)
UPPER='Le(r*((u*d)*(u*d)),r*((s*h)*(s*h))+7*((h*d)*(h*d)))'
LOWER='Le(r*((s*h)*(s*h)),r*((u*d)*(u*d))+((h*d)*(h*d)))'
CONCLUSION='Le(r*(u*d),r*(s*h)+7*(h*d)) /\\ Le(r*(s*h),r*(u*d)+(h*d))'
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> '+CONCLUSION
TARGET_SHA256='ca484cb2209e8e2ed81d29e1903feb31e830a531b0e621cf00ce722956568c9b'
HELPER_SOURCES={
    'seven':'forall a. 2*(2*a)+3*a=7*a',
    'upper':'forall '+' '.join(PARAMETERS)+'. Le(r,d) -> '+ROOT_UPPER+' -> '+HALF_UPPER+' -> '+UPPER,
    'lower':'forall '+' '.join(PARAMETERS)+'. '+ROOT_LOWER+' -> '+HALF_LOWER+' -> '+LOWER,
    'scale':'forall u h s d. Le(d,s) -> Le(h*d,u*d+s*h)',
}
HELPER_TARGET_SHA256={
    'seven':'5f0fbee2bf9e6dbd7b1c0f98fbc6401cf7ab186783c23460960d4916638098e5',
    'upper':'a2b4e3afba520eb6997679877f6ac4fce3c916e430f05cf978da9f34968afaf1',
    'lower':'99f92634191edd0a823503368bfd496d6a48f9b84d142fc0449f6a81342b1499',
    'scale':'1ec370f1746d488b1f7af8184d6cfee65bf61587947f1c6baab098cf67c4734b',
}
LINEAR_ARCHIVE=dict(case='AP048',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-square-error-linear-v1/generation-process.json.gz',
    bytes=43480,sha256='ceb81db507a666fcbb560b68d33685004d242e23af6fc1c35e1135301cdcea10',
    raw_bytes=184246,raw_sha256='41a711e8e2b02214ce40d04c37ead33ad5330ad6cbc640dc5817d936094935ad',
    bundle_bytes=36655,bundle_sha256='a69169cdb3b811afc5b43e104aae815589b7f6c60381eb67edd17d5543986487',
    nodes=31,root=30,target_ast_sha256='f1e75bcb47244d65e8f878a65bf2a5d7d7328ac4d6b03d2211b360a44946610c')
ARCHIVES=(LINEAR_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={
    'linear':LINEAR_SOURCE,'mul_ne_zero':'forall a b. ~a=0 -> ~b=0 -> ~(a*b)=0',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'add_left_mono':'forall a b c. Le(a,b) -> Le(c+a,c+b)',
    'add_right_mono':'forall a b c. Le(a,b) -> Le(a+c,b+c)',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)',
    'mul_comm':'forall a b. a*b=b*a','mul_add':'forall a b c. a*(b+c)=a*b+a*c',
    'add_assoc':'forall a b c. (a+b)+c=a+(b+c)','add_comm':'forall a b. a+b=b+a',
    'mul_succ_left':'forall a b. (S a)*b=a*b+b','one_mul':'forall a. 1*a=a',
}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES};ENDPOINT_OWNERS['linear']='AP048'
ARITHMETIC=('mul_left_mono','le_trans','mul_assoc','mul_comm','mul_add')
HELPER_DEPENDENCIES={
    'seven':('mul_succ_left','one_mul','add_assoc','add_comm'),
    'upper':ARITHMETIC+('add_left_mono','add_right_mono','add_assoc','seven'),
    'lower':ARITHMETIC,
    'scale':('mul_left_mono','mul_comm','le_trans'),
    'AP049':('upper','lower','scale','linear','mul_ne_zero','one_mul'),
}


class HalfLogRootComparisonError(ValueError):
    """Changed finite error, comparison scale, positivity or exact target."""


def frozen_half_log_root_comparison_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=5 or len(premises)!=8 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise HalfLogRootComparisonError('AP049 exact finite root comparison changed')
    return target


def source_contract():
    return dict(code='AP049',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=8,positive_denominators=['h','d'],precision_order='r<=d',
        all_supplied_half_and_root_square_bounds_preserved=True,
        finite_cross_error='r*u*d<=r*s*h+7*h*d; r*s*h<=r*u*d+h*d',
        supplied_witnesses_not_constructed=True,allows_zero_r_u=True,
        new_induction_needed=False,new_induction_count=0,new_definition_ids=[],definition_admissions=0,
        analytic_half_log_sqrt2_identity=False,analytic_limit_claim=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def half_log_root_comparison_source_pins():
    result=square_error_linear_source_pins()
    expected={'scripts/sqrt2_power_square_error_linear.py':'fe216586396fbf4b93adcfa9f084efb85a8c4879778a45593df5116e19348878',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_half_log_root_comparison.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise HalfLogRootComparisonError('finite root comparison source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _seven(s):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,parse_term
    def finish(t):
        a=t.term('a');two=parse_term('2')
        def multiple(n,arg):
            if n==1:return specialize(t,'one_mul',arg),arg
            old,expanded=multiple(n-1,arg)
            return _chain(specialize(t,'mul_succ_left',parse_term(str(n-1)),arg),CongAdd(old,EqRefl(arg))),Add(expanded,arg)
        twice,aa=multiple(2,a);double,_=multiple(2,Mul(two,a))
        four=_chain(double,CongAdd(twice,twice));triple,aaa=multiple(3,a);seven,seven_terms=multiple(7,a)
        expanded=Add(Add(aa,aa),aaa)
        return _chain(CongAdd(four,triple),_additive_equal(t,expanded,seven_terms),EqSym(seven))
    return introduce(s,('a',),(),finish)


def _scale_sum(t,registry,proof,factor,left,base,error,newleft,newbase,newerror):
    from peano_lab.kernel.proofs import CongAdd
    from peano_lab.kernel.terms import Add,Mul
    out=apply(specialize(t,'mul_left_mono',left,Add(base,error),factor),proof)
    out=_left(t,registry,out,Mul(factor,Add(base,error)),_multiplicative_equal(t,Mul(factor,left),newleft))
    expanded=_chain(specialize(t,'mul_add',factor,base,error),
        CongAdd(_multiplicative_equal(t,Mul(factor,base),newbase),_multiplicative_equal(t,Mul(factor,error),newerror)))
    return _right(t,registry,out,newleft,expanded)


def _upper(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqRefl
    from peano_lab.kernel.terms import Add,Mul,parse_term
    def finish(t):
        r,u,h,root,d=t.terms(PARAMETERS);two,three,seven=map(parse_term,('2','3','7'))
        hh,dd=Mul(h,h),Mul(d,d);X,Y,K=Mul(u,d),Mul(root,h),Mul(h,d)
        kk=Mul(K,K);U,V,B=Mul(r,Mul(X,X)),Mul(r,Mul(Y,Y)),Mul(Mul(r,two),kk)
        E=Mul(two,Mul(two,Mul(r,Mul(d,hh))));F=Mul(two,Mul(two,kk));G=Mul(three,kk)
        half=_scale_sum(t,registry,t.hyp('half'),dd,Mul(r,Mul(u,u)),Mul(Mul(r,two),hh),Mul(three,hh),U,B,G)
        root_bound=_scale_sum(t,registry,t.hyp('root'),Mul(r,hh),Mul(two,dd),Mul(root,root),Mul(two,Mul(two,d)),B,V,E)
        factor=Mul(two,Mul(two,Mul(d,hh)))
        error=apply(specialize(t,'mul_left_mono',r,d,factor),t.hyp('order'))
        error=_left(t,registry,error,Mul(factor,d),_multiplicative_equal(t,Mul(factor,r),E))
        error=_right(t,registry,error,E,_multiplicative_equal(t,Mul(factor,d),F))
        lifted=apply(specialize(t,'add_left_mono',E,F,V),error)
        upper=apply(specialize(t,'le_trans',B,Add(V,E),Add(V,F)),root_bound,lifted)
        upper=apply(specialize(t,'add_right_mono',B,Add(V,F),G),upper)
        joined=apply(specialize(t,'le_trans',U,Add(B,G),Add(Add(V,F),G)),half,upper)
        norm=_chain(specialize(t,'add_assoc',V,F,G),CongAdd(EqRefl(V),specialize(t,'seven',kk)))
        return _right(t,registry,joined,U,norm)
    return introduce(s,PARAMETERS,('order','root','half'),finish)


def _lower(s,registry):
    from peano_lab.kernel.terms import Add,Mul,parse_term
    def finish(t):
        r,u,h,root,d=t.terms(PARAMETERS);two=parse_term('2');hh,dd=Mul(h,h),Mul(d,d)
        X,Y,K=Mul(u,d),Mul(root,h),Mul(h,d);kk=Mul(K,K)
        U,V,B=Mul(r,Mul(X,X)),Mul(r,Mul(Y,Y)),Mul(Mul(r,two),kk);factor=Mul(r,hh)
        bound=apply(specialize(t,'mul_left_mono',Mul(root,root),Mul(two,dd),factor),t.hyp('root'))
        bound=_left(t,registry,bound,Mul(factor,Mul(two,dd)),_multiplicative_equal(t,Mul(factor,Mul(root,root)),V))
        bound=_right(t,registry,bound,V,_multiplicative_equal(t,Mul(factor,Mul(two,dd)),B))
        half=_scale_sum(t,registry,t.hyp('half'),dd,Mul(Mul(r,two),hh),Mul(r,Mul(u,u)),hh,B,U,kk)
        return apply(specialize(t,'le_trans',V,B,Add(U,kk)),bound,half)
    return introduce(s,PARAMETERS,('root','half'),finish)


def _scale(s,registry):
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Add,Mul
    def finish(t):
        u,h,root,d=t.terms(('u','h','s','d'));K,X,Y=Mul(h,d),Mul(u,d),Mul(root,h)
        lower=apply(specialize(t,'mul_left_mono',d,root,h),t.hyp('bound'))
        lower=_right(t,registry,lower,K,specialize(t,'mul_comm',h,root))
        return apply(specialize(t,'le_trans',K,Y,Add(X,Y)),lower,witness((X,),EqRefl(Add(X,Y))))
    return introduce(s,('u','h','s','d'),('bound',),finish)


def _root(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,parse_term
    def finish(t):
        r,u,h,root,d=t.terms(PARAMETERS);X,Y,K=Mul(u,d),Mul(root,h),Mul(h,d);one,seven=map(parse_term,('1','7'))
        upper=apply(specialize(t,'upper',r,u,h,root,d),t.hyp('order'),t.hyp('root_upper'),t.hyp('half_upper'))
        lower=apply(specialize(t,'lower',r,u,h,root,d),t.hyp('root_lower'),t.hyp('half_lower'))
        lower=_right(t,registry,lower,Mul(r,Mul(Y,Y)),CongAdd(EqRefl(Mul(r,Mul(X,X))),EqSym(specialize(t,'one_mul',Mul(K,K)))))
        scale=apply(specialize(t,'scale',u,h,root,d),t.hyp('root_bound'))
        nz=apply(specialize(t,'mul_ne_zero',h,d),t.hyp('h_nonzero'),t.hyp('d_nonzero'))
        result=apply(specialize(t,'linear',r,X,Y,K,seven,one),nz,scale,upper,lower)
        reverse=_right(t,registry,AndElimR(result),Mul(r,Y),CongAdd(EqRefl(Mul(r,X)),specialize(t,'one_mul',K)))
        return conjunction(AndElimL(result),reverse)
    return introduce(s,PARAMETERS,('h_nonzero','d_nonzero','order','root_bound','root_lower','root_upper','half_upper','half_lower'),finish)


def prove_half_log_root_comparison(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP049',target=frozen_half_log_root_comparison_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'seven':_seven,'upper':lambda s:_upper(s,registry),'lower':lambda s:_lower(s,registry),
            'scale':lambda s:_scale(s,registry),'AP049':lambda s:_root(s,registry)},
        pins=half_log_root_comparison_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
