"""AP084: all sufficiently fine actual log/exp computations are near two.

Construct one dyadic reference before quantifying over arbitrary independent
later tables. AP083 transports its error; only its positive head is cancelled.
This is a uniform finite statement, not a postulated analytic identity.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_log_exp_cutoff_refinement import (
    ROOT,Scope,introduce,eliminate,witness,apply,specialize,conjunction,field,canonical,json_hash,
    definition_registry as refinement_registry,log_exp_cutoff_refinement_source_pins,
    NAMED_SOURCE as REFINEMENT_SOURCE,COMPARISON_ARCHIVE,BOUND_ARCHIVE,
)
from sqrt2_power_log_exp_dyadic_witness import (
    NAMED_SOURCE as WITNESS_SOURCE,log_exp_dyadic_witness_source_pins,
)
from sqrt2_power_exp_two_sided_continuity import _left,_right
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-log-exp-uniform-two-v1'
M='S(S(18*r))'
REFERENCE_OUTPUTS=('r','d','ab','ac','x','p','tb','tc','h','y')
FINE_PARAMETERS=('e','bb','bc','l','z','q','N','eb','ec','b','v')
FINE_PREMISES=('~e=0',f'NatAtanhPrefix(e,bb,bc,({M})+l)',f'NatHornerValue(bb,bc,3,({M})+l,z)',
    f'Pow(3,({M})+l,q)',f'NatScaledExpRecurrence(e*q,3*z,eb,ec,(S({M}))+N)',
    'BetaAt(eb,ec,0,b)',f'Sum(eb,ec,S((S({M}))+N),v)')
BOUNDS='Le(r*v,(r*2)*b+2*b) /\\ Le((r*2)*b,r*v+b)'
FINE_CONCLUSION='~q=0 /\\ (~(e*q)=0 /\\ ('+BOUNDS+'))'
UNIFORM_SOURCE='forall '+' '.join(FINE_PARAMETERS)+'. '+' -> '.join(FINE_PREMISES)+' -> '+FINE_CONCLUSION
NAMED_SOURCE='forall n. exists r. Pow(2,n,r) /\\ (~r=0 /\\ ('+UNIFORM_SOURCE+'))'
TARGET_SHA256='018632b34699a2f0f8feb879b56eb195d89cfb1304ffe2f5da46ef3ed3607898'
HELPER_SOURCES={'arithmetic':'forall r h y b v. ~h=0 -> Le(r*y,(r*2)*h+h) -> Le((r*2)*h,r*y+h) -> Le(b*y,h*v) -> Le(r*(h*v),r*(b*y)+h*b) -> Le(r*v,(r*2)*b+2*b) /\\ Le((r*2)*b,r*v+b)'}
HELPER_TARGET_SHA256={'arithmetic':'78c0b79c467b6f495814323762845ec44ba896c59785acf70ef0a5c233840f5c'}
WITNESS_ARCHIVE=dict(case='AP034',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-log-exp-dyadic-witness-v1/generation-process.json.gz',
    bytes=176621,sha256='e7beb111df48afd373d27ee9f6f35167930459c527517e13aba3ceb3145d33f2',
    raw_bytes=4600191,raw_sha256='bf695db3a3c890caff7f3a0354b449a787708b902bcc70907b6c7a89b9392cb2',
    bundle_bytes=2812849,bundle_sha256='99ef8cd7a0cdd76a9c39d828620e1c8858565b70d202b79dfb36df034bddb63e',
    nodes=452,root=451,target_ast_sha256='c7f28f686ec9b7eb26f152b6aed3eecb9aa4b32a686ba022e3ba80d363e5f620')
REFINEMENT_ARCHIVE=dict(case='AP083',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-log-exp-cutoff-refinement-v1/generation-process.json.gz',
    bytes=89264,sha256='b94b3fa47e7d8c19a723102231f6fd09866a12f57815ff16d8ae2e1aec4c24f4',
    raw_bytes=1680264,raw_sha256='f085dde7c60c761cd5621a635e59abd333fc8af1ee5b9ba8a40e2ea49d44c507',
    bundle_bytes=995536,bundle_sha256='18275d48a04f78840e82c3d6f549a632496ea202cafc32b10de83ef2be0979fa',
    nodes=238,root=237,target_ast_sha256='97d070681313d49334933a292e949acae3f61cc484c18b5a122d05060269d1c5')
ARCHIVES=(WITNESS_ARCHIVE,REFINEMENT_ARCHIVE,COMPARISON_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'reference':WITNESS_SOURCE,'refinement':REFINEMENT_SOURCE,
    'power_exists':'forall a n. exists p. Pow(a,n,p)',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'mul_right_mono':'forall a b c. Le(a,b) -> Le(a*c,b*c)',
    'add_right_mono':'forall a b c. Le(a,b) -> Le(a+c,b+c)',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)','mul_comm':'forall a b. a*b=b*a',
    'mul_add':'forall a b c. a*(b+c)=a*b+a*c','add_mul':'forall a b c. (a+b)*c=a*c+b*c',
    'add_assoc':'forall a b c. (a+b)+c=a+(b+c)',
    'mul_succ_left':'forall a b. (S a)*b=a*b+b','one_mul':'forall a. 1*a=a',
    'mul_le_cancel':'forall c a b. ~c=0 -> Le(c*a,c*b) -> Le(a,b)'}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(reference='AP034',refinement='AP083',power_exists='AP010')
HELPER_DEPENDENCIES={'arithmetic':('mul_left_mono','mul_right_mono','add_right_mono','le_trans','mul_assoc','mul_comm',
        'mul_add','add_mul','add_assoc','mul_succ_left','one_mul','mul_le_cancel'),
    'AP084':('reference','refinement','power_exists','arithmetic')}
INPUT_SNAPSHOT='research/arithmetic-library/sqrt2-power/observations/log-exp-uniform-two-input-snapshot-v2.json'
INPUT_SNAPSHOT_BYTES=62713
INPUT_SNAPSHOT_SHA256='5474620f3586d11078cb06dd320c480d446003c30816caf4b9cf7946c21bb6ea'


class LogExpUniformTwoError(ValueError):
    """Changed uniform quantifier order, actual computation or error bound."""


def recursive_definition_registry_for_audit():
    pool=refinement_registry();result={};visiting=set();ids=set()
    def visit(name):
        if name in result:return
        if name in visiting or name not in pool:raise LogExpUniformTwoError('missing or cyclic uniform log/exp definition')
        visiting.add(name);spec=pool[name]
        for dep in spec.conceptual_dependencies:visit(dep)
        if spec.stable_id in ids:raise LogExpUniformTwoError('duplicate uniform log/exp definition identity')
        result[name]=spec;ids.add(spec.stable_id);visiting.remove(name)
    for name in ('Le','NatAtanhPrefix','NatHornerValue','Pow','NatScaledExpRecurrence','Sum'):visit(name)
    return MappingProxyType(result)


def _input_snapshot():
    with (ROOT/INPUT_SNAPSHOT).open('rb') as stream:raw=stream.read(INPUT_SNAPSHOT_BYTES+1)
    if len(raw)!=INPUT_SNAPSHOT_BYTES or sha256(raw).hexdigest()!=INPUT_SNAPSHOT_SHA256:
        raise LogExpUniformTwoError('uniform log/exp exact input snapshot changed')
    value=json.loads(raw)
    if (value.get('schema')!='sqrt2-power-log-exp-uniform-two-input-snapshot-v1'
            or value.get('authority')!='source_integrity_and_exact_definition_syntax_only_not_proof_authority'
            or len(value.get('definitions',[]))!=13 or len(value.get('source_pins',{}))!=295):
        raise LogExpUniformTwoError('uniform log/exp exact input snapshot envelope changed')
    return value


def definition_registry():
    """Reparse the exact needed templates; snapshots are syntax, not authority."""
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.library.proof_bundle import encode_formula
    result={};ids=set()
    for item in _input_snapshot()['definitions']:
        row=dict(item);digest=row.pop('template_ast_sha256')
        row['parameters']=tuple(row['parameters']);row['conceptual_dependencies']=tuple(row['conceptual_dependencies'])
        spec=_definition(**row)
        if (spec.name in result or spec.stable_id in ids
                or not set(spec.conceptual_dependencies)<=result.keys()
                or json_hash(encode_formula(spec.template_formula))!=digest):
            raise LogExpUniformTwoError('uniform log/exp conservative definition DAG changed')
        result[spec.name]=spec;ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_log_exp_uniform_two_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=1 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise LogExpUniformTwoError('AP084 exact uniform near-two target changed')
    return target


def source_contract():
    return dict(code='AP084',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,all_precisions_including_zero=True,precision_power='r=2^n',
        reference_and_precision_chosen_before_arbitrary_later_tables=True,precision_power_proved_nonzero=True,
        auxiliary_cutoff='M=18*r+2',fine_log_length='M+l',fine_exp_degree='M+1+N',
        actual_fine_logarithm_horner_power_and_exponential_computations_required=True,
        independent_scales_codes_and_heads_allowed=True,fine_argument_denominator_proved_nonzero=True,
        finite_upper_error='v/b<=2+2/r',finite_lower_error='2-1/r<=v/b',
        positive_reference_head_cancelled_only_after_proof=True,zero_l_N_and_fine_head_allowed=True,
        exact_definition_cone_reparsed_from_source_bound_snapshot=True,
        every_actual_source_rehashed_without_recursive_duplicate_reads=True,
        rational_reading_requires_positive_fine_head=True,new_induction_count=0,new_induction_needed=False,
        new_definition_ids=[],definition_admissions=0,analytic_log_exp_identity_claimed=False,analytic_limit_claimed=False,
        fixed_approximation_program_changed=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def recursive_source_pins_for_audit():
    result=log_exp_cutoff_refinement_source_pins()
    for name,pin in log_exp_dyadic_witness_source_pins().items():
        if name in result and result[name]!=pin:raise LogExpUniformTwoError('uniform log/exp dependency source disagreement')
        result[name]=pin
    expected={'scripts/sqrt2_power_log_exp_cutoff_refinement.py':'22c1f5539cf98203ad5f4750858c4b1d14aa7ba42009ff6fa6709e5f7b8ae383',
        'scripts/sqrt2_power_log_exp_dyadic_witness.py':'1545cf9e78a6f62f355e7a35fb46f88222d3bd35ace4f99bfec43a74cdf8d883',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in ('scripts/sqrt2_power_exp_two_sided_continuity.py','scripts/sqrt2_power_quadratic_height.py',
                 'scripts/sqrt2_power_finite_power_evaluation.py','scripts/sqrt2_power_mixed_assembly.py'):
        if name not in result:raise LogExpUniformTwoError('unbound uniform log/exp constructor: '+name)
    for name in (*expected,'scripts/sqrt2_power_log_exp_uniform_two.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:raise LogExpUniformTwoError('uniform log/exp source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def log_exp_uniform_two_source_pins():
    """Stream every original source once per check; retain all body replay."""
    expected=_input_snapshot()['source_pins']
    result={INPUT_SNAPSHOT:dict(bytes=INPUT_SNAPSHOT_BYTES,sha256=INPUT_SNAPSHOT_SHA256)}
    for name in (*expected,'scripts/sqrt2_power_log_exp_uniform_two.py'):
        if name.startswith('/') or '..' in name.split('/'):
            raise LogExpUniformTwoError('uniform log/exp source path escaped repository')
        bound=expected[name]['bytes'] if name in expected else 2*1024**2
        digest=sha256();size=0
        with (ROOT/name).open('rb') as stream:
            while size<=bound:
                chunk=stream.read(min(65536,bound+1-size))
                if not chunk:break
                size+=len(chunk);digest.update(chunk)
        actual=dict(bytes=size,sha256=digest.hexdigest())
        if size>bound or name in expected and actual!=expected[name]:
            raise LogExpUniformTwoError('uniform log/exp source bytes changed')
        result[name]=actual
    return result


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,parse_term
    one,two=map(parse_term,('1','2'))
    def finish(t):
        r,h,y,b,v=t.terms(('r','h','y','b','v'));R=Mul(r,two);Rh=Mul(R,h);Rb=Mul(R,b)
        Y=Mul(r,y);V=Mul(r,v);Yb=Mul(Y,b);hb=Mul(h,b);base=Mul(h,Rb);hV=Mul(h,V)
        upper=apply(specialize(t,'mul_right_mono',Y,Add(Rh,h),b),t.hyp('reference_upper'))
        rhs=_chain(specialize(t,'add_mul',Rh,h,b),CongAdd(_multiplicative_equal(t,Mul(Rh,b),base),EqRefl(hb)))
        upper=_right(t,registry,upper,Yb,rhs)
        upper=apply(specialize(t,'add_right_mono',Yb,Add(base,hb),hb),upper)
        error=_left(t,registry,t.hyp('error'),Add(Mul(r,Mul(b,y)),hb),_multiplicative_equal(t,Mul(r,Mul(h,v)),hV))
        error=_right(t,registry,error,hV,CongAdd(_multiplicative_equal(t,Mul(r,Mul(b,y)),Yb),EqRefl(hb)))
        upper=apply(specialize(t,'le_trans',hV,Add(Yb,hb),Add(Add(base,hb),hb)),error,upper)
        double=_chain(specialize(t,'mul_succ_left',one,b),CongAdd(specialize(t,'one_mul',b),EqRefl(b)))
        combine=_chain(specialize(t,'add_assoc',base,hb,hb),
            CongAdd(EqRefl(base),EqSym(specialize(t,'mul_add',h,b,b))),
            CongAdd(EqRefl(base),CongMul(EqRefl(h),EqSym(double))),EqSym(specialize(t,'mul_add',h,Rb,Mul(two,b))))
        upper=_right(t,registry,upper,hV,combine)
        upper=apply(specialize(t,'mul_le_cancel',h,V,Add(Rb,Mul(two,b))),t.hyp('nonzero_head'),upper)
        lower=apply(specialize(t,'mul_right_mono',Rh,Add(Y,h),b),t.hyp('reference_lower'))
        lower=_left(t,registry,lower,Mul(Add(Y,h),b),_multiplicative_equal(t,Mul(Rh,b),base))
        lower=_right(t,registry,lower,base,specialize(t,'add_mul',Y,h,b))
        mono=apply(specialize(t,'mul_left_mono',Mul(b,y),Mul(h,v),r),t.hyp('monotone'))
        mono=_left(t,registry,mono,Mul(r,Mul(h,v)),_multiplicative_equal(t,Mul(r,Mul(b,y)),Yb))
        mono=_right(t,registry,mono,Yb,_multiplicative_equal(t,Mul(r,Mul(h,v)),hV))
        mono=apply(specialize(t,'add_right_mono',Yb,hV,hb),mono)
        lower=apply(specialize(t,'le_trans',base,Add(Yb,hb),Add(hV,hb)),lower,mono)
        lower=_right(t,registry,lower,base,EqSym(specialize(t,'mul_add',h,V,b)))
        lower=apply(specialize(t,'mul_le_cancel',h,Rb,Add(V,b)),t.hyp('nonzero_head'),lower)
        return conjunction(upper,lower)
    return introduce(s,('r','h','y','b','v'),('nonzero_head','reference_upper','reference_lower','monotone','error'),finish)


def _root(s):
    from peano_lab.kernel.terms import Mul,Succ,parse_term
    two,eighteen=map(parse_term,('2','18'))
    def later(t):
        r,d,ab,ac,x,p,tb,tc,h,y=t.terms(REFERENCE_OUTPUTS)
        e,bb,bc,l,z,q,N,eb,ec,b,v=t.terms(FINE_PARAMETERS);P=t.term('P');data=t.hyp('reference_data')
        result=apply(specialize(t,'refinement',r,d,e,ab,ac,bb,bc,l,x,z,p,q,N,tb,tc,eb,ec,h,b,y,v,P),
            field(data,2,15),t.hyp('nonzero_e'),field(data,3,15),t.hyp('fine_log'),field(data,4,15),t.hyp('fine_value'),
            field(data,5,15),t.hyp('fine_power'),field(data,10,15),t.hyp('fine_exp'),field(data,11,15),t.hyp('fine_head'),
            field(data,12,15),t.hyp('fine_sum'),t.hyp('cutoff_power'))
        bounds=apply(specialize(t,'arithmetic',r,h,y,b,v),field(data,7,15),field(data,13,15),field(data,14,15),field(result,5,7),field(result,6,7))
        return conjunction(field(result,1,7),field(result,4,7),field(bounds,0,2),field(bounds,1,2))
    def powered(t):
        data=t.hyp('reference_data')
        universal=introduce(t,FINE_PARAMETERS,('nonzero_e','fine_log','fine_value','fine_power','fine_exp','fine_head','fine_sum'),later)
        return witness((t.term('r'),),conjunction(field(data,0,15),field(data,1,15),universal))
    def reference(t):
        M=Succ(Succ(Mul(eighteen,t.term('r'))))
        return eliminate(t,specialize(t,'power_exists',two,M),('P',),'cutoff_power',powered)
    return introduce(s,('n',),(),lambda t:eliminate(t,specialize(t,'reference',t.term('n')),REFERENCE_OUTPUTS,'reference_data',reference))


def prove_log_exp_uniform_two(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP084',target=frozen_log_exp_uniform_two_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'arithmetic':lambda s:_arithmetic(s,registry),'AP084':_root},pins=log_exp_uniform_two_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
