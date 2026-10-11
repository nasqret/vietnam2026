"""AP092: constructed fixed half-log samples versus any supplied finer root.

AP091 chooses a coarse root before later indices. SQ008 bounds its distance
from every supplied root at n+l. Natural arithmetic transfers both errors,
retaining all actual positive-normalized witnesses at that same index n+l.
This is a finite comparison, not an analytic identification or irrationality.
"""
from hashlib import sha256
import re

from sqrt2_power_fixed_half_log_root_witness import (
    ROOT,Scope,introduce,eliminate,witness,apply,specialize,conjunction,field,canonical,json_hash,
    definition_registry,fixed_half_log_root_witness_source_pins,NAMED_SOURCE as WITNESS_SOURCE,
    PARTS as WITNESS_PARTS,OUTPUTS,conjoin,
)
from sqrt2_power_dyadic_sqrt2_modulus import NAMED_SOURCE as MODULUS_SOURCE,dyadic_sqrt2_modulus_source_pins
from sqrt2_power_dyadic_sqrt2_square_error import NAMED_SOURCE as SQUARE_SOURCE
from sqrt2_power_dyadic_sqrt2_reciprocal import MODULUS_ARCHIVE
from sqrt2_power_scaled_exp_tail import BOUND_ARCHIVE
from sqrt2_power_exp_two_sided_continuity import _left,_right
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-fixed-half-log-fine-root-v1'
BOUNDS=('Le(r*(e*y),r*(t*h)+8*(e*h))','Le(r*(t*h),r*(e*y)+2*(e*h))')
PARTS=tuple(re.sub(r'\bk\b','(n+l)',part) for part in WITNESS_PARTS[:17])+('~e=0','~t=0','Le(e,t)','Lt(t,2*e)')+BOUNDS
LATER_SOURCE='forall l e t. DyadicSqrt2(n+l,e,t) -> Le(S(S(18*r)),n+l) -> exists '+' '.join(OUTPUTS)+'. '+conjoin(PARTS)
NAMED_SOURCE='forall n. exists r. Pow(2,n,r) /\\ (~r=0 /\\ ('+LATER_SOURCE+'))'
TARGET_SHA256='6d4b5804c59942bc029957cbb384a3a6d2235616d7c0e1cf4c0af32be3e12771'
HELPER_SOURCES={'arithmetic':'forall r s e t h y. Le(r*y,s*h+8*h) -> Le(s*h,r*y+h) -> Le(s*e,t*r) -> Le(t*r,s*e+e) -> '+conjoin(BOUNDS)}
HELPER_TARGET_SHA256={'arithmetic':'29e6869a859b6574ae57e2d59c9f33a46ee5f500d8bb99cb0c3602df0ddee974'}
WITNESS_ARCHIVE=dict(case='AP091',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-half-log-root-witness-v1/generation-process.json.gz',
    bytes=241364,sha256='8977bb12e08e690f836754a9d9ef1bbb3cac50d197bf4fc6f5029ae18e40623f',
    raw_bytes=6387409,raw_sha256='6d6d5b32d8dab4fa5beb817b3b911ad88711fd7ff274ae6c2ccac2bb2bc85a98',
    bundle_bytes=3913686,bundle_sha256='ca771f818bb607d30de80c5bc19a15ee2d05a0932355fc71c7800b0ef096d67b',
    nodes=586,root=585,target_ast_sha256='9fba277808e08f9fc794a636d0be0242f1a8498dbd631870d0f88440174b708a')
ARCHIVES=(WITNESS_ARCHIVE,MODULUS_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'witnesses':WITNESS_SOURCE,'modulus':MODULUS_SOURCE,'square':SQUARE_SOURCE,
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'add_right_mono':'forall a b c. Le(a,b) -> Le(a+c,b+c)',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)','mul_comm':'forall a b. a*b=b*a',
    'mul_add':'forall a b c. a*(b+c)=a*b+a*c','add_assoc':'forall a b c. (a+b)+c=a+(b+c)',
    'mul_succ_left':'forall a b. (S a)*b=a*b+b','one_mul':'forall a. 1*a=a'}
ENDPOINT_OWNERS={name:'AP091' for name in ENDPOINT_SOURCES};ENDPOINT_OWNERS['modulus']='SQ008'
ENDPOINT_OWNERS['mul_left_mono']='CV071'
HELPER_DEPENDENCIES={'arithmetic':tuple(name for name in ENDPOINT_SOURCES if name not in ('witnesses','modulus','square')),
    'AP092':('witnesses','modulus','square','arithmetic')}


class FixedHalfLogFineRootError(ValueError):
    """Changed supplied fine root, actual witnesses, index alignment or bounds."""


def frozen_fixed_half_log_fine_root_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=1 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise FixedHalfLogFineRootError('AP092 exact supplied-finer-root witness target changed')
    return target


def source_contract():
    return dict(code='AP092',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,all_precisions_and_finer_increments_including_zero=True,
        actual_power_chosen_before_all_later_supplied_roots=True,supplied_fine_root='DyadicSqrt2(n+l,e,t)',
        sufficient_threshold='18*r+2<=n+l',sample_and_fine_root_index='n+l',
        fixed_logarithm_prefix_length='2*(n+l)+1',fixed_exp_degree='(n+l)+2',
        all_thirteen_AP091_witnesses_retained=True,positive_fine_denominator_and_root_proved=True,
        fine_root_bounds='e<=t<2*e',all_factorial_normalizations_retained=True,
        finite_cross_bounds=list(BOUNDS),finite_rational_error='-2/r<=y/h-t/e<=8/r',
        old_upper_error_preserved=True,reverse_error_components=[1,1],
        new_definition_ids=[],definition_admissions=0,new_induction_count=0,new_induction_needed=False,
        new_solver_arithmetic_leaf='AP092-arithmetic',solver_hints_are_proof_authority=False,
        analytic_limit_claimed=False,analytic_half_log_sqrt2_identity_claimed=False,
        root_quotient_accuracy_claimed=False,fixed_approximation_program_changed=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def fixed_half_log_fine_root_source_pins():
    result=fixed_half_log_root_witness_source_pins()
    for name,pin in dyadic_sqrt2_modulus_source_pins().items():
        if name in result and result[name]!=pin:raise FixedHalfLogFineRootError('inherited modulus source changed')
        result[name]=pin
    expected={pin['path']:dict(bytes=pin['bytes'],sha256=pin['sha256']) for pin in ARCHIVES}
    for name in ('scripts/sqrt2_power_dyadic_sqrt2_reciprocal.py','scripts/sqrt2_power_dyadic_sqrt2_square_error.py',
            'scripts/sqrt2_power_exp_two_sided_continuity.py','scripts/sqrt2_power_quadratic_height.py',
            'scripts/sqrt2_power_finite_power_evaluation.py','scripts/sqrt2_power_mixed_assembly.py'):
        if name not in result:raise FixedHalfLogFineRootError('unbound imported constructor: '+name)
    for name in (*expected,'scripts/sqrt2_power_fixed_half_log_fine_root.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        pin=dict(bytes=len(raw),sha256=sha256(raw).hexdigest())
        if len(raw)>2*1024**2 or name in expected and pin!=expected[name]:
            raise FixedHalfLogFineRootError('fine-root source or archive changed')
        result[name]=pin
    return result


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,parse_term
    def finish(u):
        r,coarse,e,fine,h,y=u.terms(('r','s','e','t','h','y'));one,two,eight=map(parse_term,('1','2','8'))
        X,Y,K=Mul(r,Mul(e,y)),Mul(r,Mul(fine,h)),Mul(e,h)
        Z=Mul(Mul(coarse,e),h);E=Mul(eight,K)
        def scale_sum(proof,factor,a,b,c,left,base,error):
            p=apply(specialize(u,'mul_left_mono',a,Add(b,c),factor),proof)
            p=_left(u,registry,p,Mul(factor,Add(b,c)),_multiplicative_equal(u,Mul(factor,a),left))
            equal=_chain(specialize(u,'mul_add',factor,b,c),
                CongAdd(_multiplicative_equal(u,Mul(factor,b),base),_multiplicative_equal(u,Mul(factor,c),error)))
            return _right(u,registry,p,left,equal)
        upper=scale_sum(u.hyp('sample_upper'),e,Mul(r,y),Mul(coarse,h),Mul(eight,h),X,Z,E)
        root=apply(specialize(u,'mul_left_mono',Mul(coarse,e),Mul(fine,r),h),u.hyp('root_lower'))
        root=_left(u,registry,root,Mul(h,Mul(fine,r)),_multiplicative_equal(u,Mul(h,Mul(coarse,e)),Z))
        root=_right(u,registry,root,Z,_multiplicative_equal(u,Mul(h,Mul(fine,r)),Y))
        root=apply(specialize(u,'add_right_mono',Z,Y,E),root)
        upper=apply(specialize(u,'le_trans',X,Add(Z,E),Add(Y,E)),upper,root)
        lower=scale_sum(u.hyp('root_upper'),h,Mul(fine,r),Mul(coarse,e),e,Y,Z,K)
        sample=scale_sum(u.hyp('sample_lower'),e,Mul(coarse,h),Mul(r,y),h,Z,X,K)
        sample=apply(specialize(u,'add_right_mono',Z,Add(X,K),K),sample)
        lower=apply(specialize(u,'le_trans',Y,Add(Z,K),Add(Add(X,K),K)),lower,sample)
        double=_chain(specialize(u,'mul_succ_left',one,K),CongAdd(specialize(u,'one_mul',K),EqRefl(K)))
        normalized=_chain(specialize(u,'add_assoc',X,K,K),CongAdd(EqRefl(X),EqSym(double)))
        return conjunction(upper,_right(u,registry,lower,Y,normalized))
    return introduce(s,('r','s','e','t','h','y'),('sample_upper','sample_lower','root_lower','root_upper'),finish)


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.terms import Add
    def constructed(u):
        n,l,r,coarse,e,fine,h,y=u.terms(('n','l','r','s','e','t','h','y'));data=u.hyp('sample')
        modulus=apply(specialize(u,'modulus',n,l,r,coarse,e,fine),field(u.hyp('reference'),2,4),u.hyp('fine_root'))
        square=apply(specialize(u,'square',Add(n,l),e,fine),u.hyp('fine_root'))
        bounds=apply(specialize(u,'arithmetic',r,coarse,e,fine,h,y),field(data,17,19),field(data,18,19),
            field(modulus,2,4),field(modulus,3,4))
        return witness(u.terms(OUTPUTS),conjunction(*(field(data,i,19) for i in range(17)),
            *(field(square,i,6) for i in range(4)),field(bounds,0,2),field(bounds,1,2)))
    def later(u):
        actual=apply(instantiate(field(u.hyp('reference'),3,4),Add(u.term('n'),u.term('l'))),u.hyp('threshold'))
        return eliminate(u,actual,OUTPUTS,'sample',constructed)
    def chosen(u):
        later_proof=introduce(u,('l','e','t'),('fine_root','threshold'),later)
        return witness((u.term('r'),),conjunction(field(u.hyp('reference'),0,4),field(u.hyp('reference'),1,4),later_proof))
    return introduce(s,('n',),(),lambda u:eliminate(u,specialize(u,'witnesses',u.term('n')),('r','s'),'reference',chosen))


def factories(registry):return {'arithmetic':lambda s:_arithmetic(s,registry),'AP092':_root}


def prove_fixed_half_log_fine_root(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP092',target=frozen_fixed_half_log_fine_root_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories(registry),
        pins=fixed_half_log_fine_root_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
