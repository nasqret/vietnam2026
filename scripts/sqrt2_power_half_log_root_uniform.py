"""AP089: all sufficiently late half-log exponentials approach one dyadic root.

Construct the actual reference before arbitrary later independent tables.
Restrict its actual recurrence, apply the proved half-log cutoff, and cancel
only proved positive factors. This is a finite bridge, not a real limit axiom.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_half_log_root_witness import (
    ROOT,Scope,introduce,eliminate,witness,apply,specialize,conjunction,field,canonical,json_hash,
    NAMED_SOURCE as REFERENCE_SOURCE,definition_registry as reference_registry,half_log_root_witness_source_pins,
)
from sqrt2_power_half_log_square import half_log_square_source_pins
from sqrt2_power_half_log_exp_cutoff import (
    NAMED_SOURCE as REFINEMENT_SOURCE,definition_registry as refinement_registry,half_log_exp_cutoff_source_pins,
)
from sqrt2_power_log_exp_cutoff_refinement import COMPARISON_ARCHIVE,BOUND_ARCHIVE
from sqrt2_power_log_exp_refinement import TWO_ERROR_ARCHIVE
from sqrt2_power_exp_two_error_bound import HELPER_SOURCES as EXP_HELPERS
from sqrt2_power_exp_two_sided_continuity import _left,_right
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-half-log-root-uniform-v1'
M='S(S(18*r))'
REFERENCE_OUTPUTS=('r','d','lb','lc','x','p','wb','wc','cb','cc','h','f','T','y','u','s')
FINE_PARAMETERS=('e','bb','bc','l','z','q','N','eb','ec','b','v')
FINE_PREMISES=('~e=0',f'NatAtanhPrefix(e,bb,bc,({M})+l)',f'NatHornerValue(bb,bc,3,({M})+l,z)',
    f'Pow(3,({M})+l,q)',f'NatScaledExpRecurrence(2*(e*q),3*z,eb,ec,(S({M}))+N)',
    'BetaAt(eb,ec,0,b)',f'Sum(eb,ec,S((S({M}))+N),v)')
BOUNDS='Le(r*v,s*b+8*b) /\\ Le(s*b,r*v+b)'
FINE_CONCLUSION='~q=0 /\\ (~(2*(e*q))=0 /\\ ('+BOUNDS+'))'
UNIFORM_SOURCE='forall '+' '.join(FINE_PARAMETERS)+'. '+' -> '.join(FINE_PREMISES)+' -> '+FINE_CONCLUSION
NAMED_SOURCE='forall n. exists r s. Pow(2,n,r) /\\ (~r=0 /\\ (DyadicSqrt2(n,r,s) /\\ ('+UNIFORM_SOURCE+')))'
TARGET_SHA256='bdd05acec456f38c8dbd660093564668cdcb6a6207fd285396940740dcf42ff8'
HELPER_SOURCES={'arithmetic':'forall r s h u b v. ~r=0 -> ~h=0 -> Le(r*(u*r),r*(s*h)+7*(h*r)) -> Le(r*(s*h),r*(u*r)+(h*r)) -> Le(b*u,h*v) -> Le(r*(h*v),r*(b*u)+h*b) -> '+BOUNDS}
HELPER_TARGET_SHA256={'arithmetic':'9f71319113d5bd34c4e47709066536f754bce5a6b84da84e5fa69e5d0f6fb5f2'}
REFERENCE_ARCHIVE=dict(case='AP050',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-half-log-root-witness-v1/generation-process.json.gz',
    bytes=220490,sha256='7e64aa16740e22d6a6ecc3b57272db7f15cb9251ee2f8ac9d3fe513b9258216e',
    raw_bytes=5774507,raw_sha256='c8ffdb53236639c714e5b4721cfe02bf1d7321ec88fc5f8ac89c5a08f4b7c0ad',
    bundle_bytes=3534091,bundle_sha256='7c36ebfc20bc30b67500cb3c89192873f059af2f30b2cf4f26baeb80c3d822b6',
    nodes=560,root=559,target_ast_sha256='4110740f69dfccac4fd2f8dfa027de161e05948d42f010fe33bdf3b03c1bcbca')
REFINEMENT_ARCHIVE=dict(case='AP088',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-half-log-exp-cutoff-v1/generation-process.json.gz',
    bytes=89363,sha256='2dc945ac420b4fd69c0c3eee16a4d86fa3a394e9124c4ecfee209c5d9822875f',
    raw_bytes=1733316,raw_sha256='5917e653215a405ec5c303ad34be63daa250c152a494a1da745f2882b74ddc8a',
    bundle_bytes=1030455,bundle_sha256='2c3fe08cb08b747f0bfb835ea226855277aebb872f9f587736be3e74c22da8cc',
    nodes=240,root=239,target_ast_sha256='da6645f80e599d951709a835b4f07996fb457ad7c848fe65a66fb2ed76dbf5b0')
ARCHIVES=(REFERENCE_ARCHIVE,REFINEMENT_ARCHIVE,TWO_ERROR_ARCHIVE,COMPARISON_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'reference':REFERENCE_SOURCE,'refinement':REFINEMENT_SOURCE,'restrict':EXP_HELPERS['restrict'],
    'power_exists':'forall a n. exists p. Pow(a,n,p)',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'add_right_mono':'forall a b c. Le(a,b) -> Le(a+c,b+c)',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)','mul_comm':'forall a b. a*b=b*a',
    'mul_add':'forall a b c. a*(b+c)=a*b+a*c','add_assoc':'forall a b c. (a+b)+c=a+(b+c)',
    'mul_succ_left':'forall a b. (S a)*b=a*b+b','mul_le_cancel':'forall c a b. ~c=0 -> Le(c*a,c*b) -> Le(a,b)'}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(reference='AP050',refinement='AP088',restrict='CV101',power_exists='AP010')
HELPER_DEPENDENCIES={'arithmetic':tuple(name for name in ENDPOINT_SOURCES if name not in ('reference','refinement','restrict','power_exists')),
    'AP089':('reference','refinement','restrict','power_exists','arithmetic')}
INPUT_SNAPSHOT='research/arithmetic-library/sqrt2-power/observations/half-log-root-uniform-input-snapshot-v1.json'
INPUT_SNAPSHOT_BYTES=80682
INPUT_SNAPSHOT_SHA256='e6350f66b76b45f3699a3c769b6fd459fddec1ca21ad5fe290510ebd772fb48c'
INPUT_SOURCE_COUNT=352
INPUT_DEFINITION_COUNT=19


class HalfLogRootUniformError(ValueError):
    """Changed independent half-logarithm data, root witness or finite bound."""


def recursive_definition_registry_for_audit():
    pool=dict(reference_registry());identity=('stable_id','name','parameters','template_source','template_formula','conceptual_dependencies')
    for name,spec in refinement_registry().items():
        if name in pool:
            if any(getattr(pool[name],key)!=getattr(spec,key) for key in identity):
                raise HalfLogRootUniformError('shared half-log/root definition changed')
        else:pool[name]=spec
    result={};visiting=set();ids=set()
    def visit(name):
        if name in result:return
        if name in visiting or name not in pool:raise HalfLogRootUniformError('missing or cyclic half-log/root definition')
        visiting.add(name);spec=pool[name]
        for dep in spec.conceptual_dependencies:visit(dep)
        if spec.stable_id in ids:raise HalfLogRootUniformError('duplicate half-log/root definition identity')
        result[name]=spec;ids.add(spec.stable_id);visiting.remove(name)
    for name in ('Le','DyadicSqrt2','NatAtanhPrefix','NatHornerValue','Pow','NatScaledExpRecurrence','Sum',
                 'NatExpWeightTable','NatPowerWeightedPrefix','Factorial'):visit(name)
    return MappingProxyType(result)


def _input_snapshot():
    with (ROOT/INPUT_SNAPSHOT).open('rb') as stream:raw=stream.read(INPUT_SNAPSHOT_BYTES+1)
    if len(raw)!=INPUT_SNAPSHOT_BYTES or sha256(raw).hexdigest()!=INPUT_SNAPSHOT_SHA256:
        raise HalfLogRootUniformError('half-log/root exact input snapshot changed')
    value=json.loads(raw)
    if (value.get('schema')!='sqrt2-power-half-log-root-uniform-input-snapshot-v1'
            or value.get('authority')!='source_integrity_and_exact_definition_syntax_only_not_proof_authority'
            or len(value.get('definitions',[]))!=INPUT_DEFINITION_COUNT or len(value.get('source_pins',{}))!=INPUT_SOURCE_COUNT):
        raise HalfLogRootUniformError('half-log/root input envelope changed')
    return value


def definition_registry():
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.library.proof_bundle import encode_formula
    result={};ids=set()
    for item in _input_snapshot()['definitions']:
        row=dict(item);digest=row.pop('template_ast_sha256')
        row['parameters']=tuple(row['parameters']);row['conceptual_dependencies']=tuple(row['conceptual_dependencies'])
        spec=_definition(**row)
        if (spec.name in result or spec.stable_id in ids or not set(spec.conceptual_dependencies)<=result.keys()
                or json_hash(encode_formula(spec.template_formula))!=digest):raise HalfLogRootUniformError('half-log/root conservative definition DAG changed')
        result[spec.name]=spec;ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_half_log_root_uniform_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=1 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise HalfLogRootUniformError('AP089 exact uniform half-log/root target changed')
    return target


def source_contract():
    return dict(code='AP089',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,all_precisions_including_zero=True,actual_precision_power='r=2^n',
        actual_reference_and_dyadic_root_chosen_before_all_later_independent_tables=True,
        root_computation_retained='DyadicSqrt2(n,r,s)',auxiliary_cutoff='M=18*r+2',
        original_logarithm_scales_and_computations_unchanged=True,actual_half_arguments_explicit=True,
        reference_recurrence_restricted_from='H=(M+1)+M',reference_recurrence_restricted_to='M',
        fine_log_length='M+l',fine_exp_degree='M+1+N',both_actual_cutoff_powers_constructed=True,
        cancellation_requires_positive_reference_scale_and_head=True,upper_error_components=[7,1],
        finite_cross_bounds=['r*v<=s*b+8*b','s*b<=r*v+b'],finite_rational_error='-1/r<=v/b-s/r<=8/r',
        zero_fine_head_l_and_N_allowed=True,rational_reading_requires_positive_fine_head=True,
        exact_definition_cone_reparsed_from_source_bound_snapshot=True,every_actual_source_rehashed=True,
        new_induction_count=0,new_induction_needed=False,new_definition_ids=[],definition_admissions=0,
        analytic_half_log_sqrt2_identity_claimed=False,analytic_limit_claimed=False,fixed_approximation_program_changed=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def recursive_source_pins_for_audit():
    result=half_log_root_witness_source_pins()
    for source in (half_log_square_source_pins,half_log_exp_cutoff_source_pins):
        for name,pin in source().items():
            if name in result and result[name]!=pin:raise HalfLogRootUniformError('half-log/root source closure disagreement')
            result[name]=pin
    expected={'scripts/sqrt2_power_half_log_root_witness.py':'d0fc0dd950fb9d98194c9c89a8c2efccee2a0e2e74bbd6a4827528048b86d9a0',
        'scripts/sqrt2_power_half_log_square.py':'4a65a86196f134092448c7a8601da69d9ff499e22571f7015a3d49975d7bb5b6',
        'scripts/sqrt2_power_half_log_exp_cutoff.py':'b77f61e1121e219bee074198cd326da6f8ddbdbf93f54816440795f0ebf1440a',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in ('scripts/sqrt2_power_exp_two_error_bound.py','scripts/sqrt2_power_log_exp_cutoff_refinement.py',
                 'scripts/sqrt2_power_log_exp_refinement.py','scripts/sqrt2_power_mixed_assembly.py'):
        if name not in result:raise HalfLogRootUniformError('unbound half-log/root imported source: '+name)
    for name in (*expected,'scripts/sqrt2_power_half_log_root_uniform.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise HalfLogRootUniformError('half-log/root source or archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def half_log_root_uniform_source_pins():
    expected=_input_snapshot()['source_pins'];result={INPUT_SNAPSHOT:dict(bytes=INPUT_SNAPSHOT_BYTES,sha256=INPUT_SNAPSHOT_SHA256)}
    for name in (*expected,'scripts/sqrt2_power_half_log_root_uniform.py'):
        if name.startswith('/') or '..' in name.split('/'):raise HalfLogRootUniformError('half-log/root source path escaped repository')
        bound=expected[name]['bytes'] if name in expected else 2*1024**2;digest=sha256();size=0
        with (ROOT/name).open('rb') as stream:
            while size<=bound:
                chunk=stream.read(min(65536,bound+1-size))
                if not chunk:break
                size+=len(chunk);digest.update(chunk)
        actual=dict(bytes=size,sha256=digest.hexdigest())
        if size>bound or name in expected and actual!=expected[name]:raise HalfLogRootUniformError('half-log/root actual source bytes changed')
        result[name]=actual
    return result


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,parse_term
    seven,eight=map(parse_term,('7','8'))
    def finish(t):
        r,root,h,u,b,v=t.terms(('r','s','h','u','b','v'))
        ur,sh,hr=Mul(u,r),Mul(root,h),Mul(h,r)
        rur,rsh=Mul(r,ur),Mul(r,sh);sevenh=Mul(seven,h)
        upper=_right(t,registry,t.hyp('reference_upper'),rur,
            _chain(CongAdd(EqRefl(rsh),_multiplicative_equal(t,Mul(seven,hr),Mul(r,sevenh))),
                   EqSym(specialize(t,'mul_add',r,sh,sevenh))))
        upper=apply(specialize(t,'mul_le_cancel',r,ur,Add(sh,sevenh)),t.hyp('positive_r'),upper)
        lower=_right(t,registry,t.hyp('reference_lower'),rsh,
            _chain(CongAdd(EqRefl(rur),specialize(t,'mul_comm',h,r)),EqSym(specialize(t,'mul_add',r,ur,h))))
        lower=apply(specialize(t,'mul_le_cancel',r,sh,Add(ur,h)),t.hyp('positive_r'),lower)
        rv,sb=Mul(r,v),Mul(root,b);hb=Mul(h,b);base=Mul(h,sb);rbu=Mul(r,Mul(b,u));rhv=Mul(r,Mul(h,v))
        upper=apply(specialize(t,'mul_left_mono',ur,Add(sh,sevenh),b),upper)
        upper=_left(t,registry,upper,Mul(b,Add(sh,sevenh)),_multiplicative_equal(t,Mul(b,ur),rbu))
        upper=_right(t,registry,upper,rbu,
            _chain(specialize(t,'mul_add',b,sh,sevenh),
                   CongAdd(_multiplicative_equal(t,Mul(b,sh),base),_multiplicative_equal(t,Mul(b,sevenh),Mul(seven,hb)))))
        upper=apply(specialize(t,'add_right_mono',rbu,Add(base,Mul(seven,hb)),hb),upper)
        upper=apply(specialize(t,'le_trans',rhv,Add(rbu,hb),Add(Add(base,Mul(seven,hb)),hb)),t.hyp('error'),upper)
        hrv=Mul(h,rv)
        upper=_left(t,registry,upper,Add(Add(base,Mul(seven,hb)),hb),_multiplicative_equal(t,rhv,hrv))
        rhs=_chain(specialize(t,'add_assoc',base,Mul(seven,hb),hb),
            CongAdd(EqRefl(base),EqSym(specialize(t,'mul_succ_left',seven,hb))),
            CongAdd(EqRefl(base),_multiplicative_equal(t,Mul(eight,hb),Mul(h,Mul(eight,b)))),
            EqSym(specialize(t,'mul_add',h,sb,Mul(eight,b))))
        upper=_right(t,registry,upper,hrv,rhs)
        upper=apply(specialize(t,'mul_le_cancel',h,rv,Add(sb,Mul(eight,b))),t.hyp('positive_head'),upper)
        lower=apply(specialize(t,'mul_left_mono',sh,Add(ur,h),b),lower)
        lower=_left(t,registry,lower,Mul(b,Add(ur,h)),_multiplicative_equal(t,Mul(b,sh),base))
        lower=_right(t,registry,lower,base,
            _chain(specialize(t,'mul_add',b,ur,h),CongAdd(_multiplicative_equal(t,Mul(b,ur),rbu),specialize(t,'mul_comm',b,h))))
        mono=apply(specialize(t,'mul_left_mono',Mul(b,u),Mul(h,v),r),t.hyp('monotone'))
        mono=apply(specialize(t,'add_right_mono',rbu,rhv,hb),mono)
        lower=apply(specialize(t,'le_trans',base,Add(rbu,hb),Add(rhv,hb)),lower,mono)
        lower=_right(t,registry,lower,base,
            _chain(CongAdd(_multiplicative_equal(t,rhv,hrv),EqRefl(hb)),EqSym(specialize(t,'mul_add',h,rv,b))))
        lower=apply(specialize(t,'mul_le_cancel',h,sb,Add(rv,b)),t.hyp('positive_head'),lower)
        return conjunction(upper,lower)
    return introduce(s,('r','s','h','u','b','v'),('positive_r','positive_head','reference_upper','reference_lower','monotone','error'),finish)


def _root(s,registry):
    from peano_lab.kernel.proofs import Cut,EqRefl
    from peano_lab.kernel.terms import Add,Mul,Succ,parse_term
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_half_log_exp_cutoff import CONCLUSION as REFINEMENT_CONCLUSION
    two,three,eighteen=map(parse_term,('2','3','18'))
    def refined(t):
        r,root,h,u,b,v=t.terms(('r','s','h','u','b','v'))
        data=t.hyp('reference_data');result=t.hyp('refinement_data')
        bounds=apply(specialize(t,'arithmetic',r,root,h,u,b,v),field(data,1,25),field(data,9,25),
            field(data,23,25),field(data,24,25),field(result,5,7),field(result,6,7))
        inside=t.hypothesis('bounds_data');bound_hyp=inside.hyp('bounds_data');result_hyp=inside.hyp('refinement_data')
        body=conjunction(field(result_hyp,1,7),field(result_hyp,4,7),field(bound_hyp,0,2),field(bound_hyp,1,2))
        return Cut(parse_named(BOUNDS,t.variables,registry),parse_named(FINE_CONCLUSION,t.variables,registry),bounds,body)
    def later(t):
        r,d,lb,lc,x,p,wb,wc,cb,cc,h,f,T,y,u,root=t.terms(REFERENCE_OUTPUTS)
        e,bb,bc,l,z,q,N,eb,ec,b,v=t.terms(FINE_PARAMETERS);P=t.term('P');data=t.hyp('reference_data')
        M=Succ(Succ(Mul(eighteen,r)));H=Add(Succ(M),M)
        prefix=apply(specialize(t,'restrict',Mul(two,Mul(d,p)),Mul(three,x),cb,cc,M,H),
            witness((Succ(M),),EqRefl(H)),field(data,18,25))
        result=apply(specialize(t,'refinement',r,d,e,lb,lc,bb,bc,l,x,z,p,q,N,cb,cc,eb,ec,h,b,u,v,P),
            field(data,2,25),t.hyp('nonzero_e'),field(data,3,25),t.hyp('fine_log'),field(data,4,25),t.hyp('fine_value'),
            field(data,5,25),t.hyp('fine_power'),prefix,t.hyp('fine_exp'),field(data,13,25),t.hyp('fine_head'),
            field(data,19,25),t.hyp('fine_sum'),t.hyp('cutoff_power'))
        proposition=REFINEMENT_CONCLUSION.replace('a0','h').replace('b0','b')
        return Cut(parse_named(proposition,t.variables,registry),parse_named(FINE_CONCLUSION,t.variables,registry),
            result,refined(t.hypothesis('refinement_data')))
    def powered(t):
        data=t.hyp('reference_data')
        universal=introduce(t,FINE_PARAMETERS,('nonzero_e','fine_log','fine_value','fine_power','fine_exp','fine_head','fine_sum'),later)
        return witness((t.term('r'),t.term('s')),conjunction(field(data,0,25),field(data,1,25),field(data,22,25),universal))
    def reference(t):
        M=Succ(Succ(Mul(eighteen,t.term('r'))))
        return eliminate(t,specialize(t,'power_exists',two,M),('P',),'cutoff_power',powered)
    return introduce(s,('n',),(),lambda t:eliminate(t,specialize(t,'reference',t.term('n')),REFERENCE_OUTPUTS,'reference_data',reference))


def prove_half_log_root_uniform(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP089',target=frozen_half_log_root_uniform_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'arithmetic':lambda s:_arithmetic(s,registry),'AP089':lambda s:_root(s,registry)},pins=half_log_root_uniform_source_pins,
        contract=dict(source_contract(),existing_checked_cut_nodes_introduced=2,
            repair_scope='share_only_the_instantiated_refinement_and_final_error_pair_in_the_new_root'),
        limits=limits,new_induction_count=0)
