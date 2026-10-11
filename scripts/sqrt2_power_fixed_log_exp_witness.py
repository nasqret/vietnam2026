"""AP086: construct positive fixed-schedule log/exp samples near two.

Choose the dyadic threshold before arbitrary later indices, then construct
the actual logarithm table, its value and power, and positive factorial-
normalized exponential terms. No convergence premise or analytic axiom.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_fixed_log_exp_convergence import (
    ROOT,Scope,introduce,eliminate,witness,apply,specialize,conjunction,field,canonical,json_hash,
    definition_registry as fixed_registry,fixed_log_exp_convergence_source_pins,
    NAMED_SOURCE as FIXED_SOURCE,BOUND_ARCHIVE,
)
from sqrt2_power_log_exp_uniform_two import COMPARISON_ARCHIVE
from sqrt2_power_atanh_coefficients import (
    NAMED_SOURCE as ATANH_SOURCE,definition_registry as coefficient_registry,atanh_coefficients_source_pins,
)
from sqrt2_power_scaled_exp_terms import (
    NAMED_SOURCE as EXP_SOURCE,definition_registry as exp_registry,scaled_exp_terms_source_pins,COMPOSITION_ARCHIVE,
)
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-fixed-log-exp-witness-v1'
OUTPUTS=('d','ab','ac','x','p','wb','wc','tb','tc','h','f','q','y')
EXP_OUTPUTS=('wb','wc','tb','tc','h','f','q','y')
NORMALIZATION='forall j a fj dj xj. Le(j,S(S k)) -> BetaAt(tb,tc,j,a) -> Factorial(j,fj) -> Pow(d*p,j,dj) -> Pow(3*x,j,xj) -> (a*fj)*dj=h*xj'
PARTS=('~d=0','NatAtanhPrefix(d,ab,ac,S(2*k))','NatHornerValue(ab,ac,3,S(2*k),x)',
    'Pow(3,S(2*k),p)','~p=0','~(d*p)=0',
    'NatExpWeightTable(d*p,S(S k),wb,wc)','NatPowerWeightedPrefix(3*x,wb,wc,tb,tc,S(S(S k)))',
    'BetaAt(wb,wc,0,h)','BetaAt(tb,tc,0,h)','~h=0','Factorial(S(S k),f)','Pow(d*p,S(S k),q)','h=f*q',
    'Sum(tb,tc,S(S(S k)),y)','NatScaledExpRecurrence(d*p,3*x,tb,tc,S(S k))',NORMALIZATION,
    'Le(r*y,(r*2)*h+2*h)','Le((r*2)*h,r*y+h)')


def conjoin(parts):
    result=parts[-1]
    for part in reversed(parts[:-1]):result=f'({part}) /\\ ({result})'
    return result


LATER_SOURCE='forall k. Le(S(S(18*r)),k) -> exists '+' '.join(OUTPUTS)+'. '+conjoin(PARTS)
NAMED_SOURCE='forall n. exists r. Pow(2,n,r) /\\ (~r=0 /\\ ('+LATER_SOURCE+'))'
TARGET_SHA256='3ff68dfaeccdb0e61f146f12e87cf0d13b773fc609d14b0ad64a489af6b11d33'
FIXED_ARCHIVE=dict(case='AP085',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-log-exp-convergence-v1/generation-process.json.gz',
    bytes=206369,sha256='966014b2b7f9fe91417d0007c65e8af332463e1043cb515f45f664541bf83d5e',
    raw_bytes=5432179,raw_sha256='43924032fc3a0a1f7716cc29500bd8f208c80352c606d137577e35a04eea75c7',
    bundle_bytes=3330729,bundle_sha256='68e17a66cae013163f697f1a85a48dc2d9a05b8f84a2c621b5a3ca15547cf2a7',
    nodes=513,root=512,target_ast_sha256='c49cb9e52773c0bae1157f7b1eedbc0f29391c3163cb80a3c9c28445c69c37b1')
ATANH_ARCHIVE=dict(case='CV025',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-atanh-coefficients-v1/generation-process.json.gz',
    bytes=19131,sha256='56d2ead6b78500ead3fd14dbd7e252b7310b31b163b5be133743f2ee295be216',
    raw_bytes=277456,raw_sha256='b7c31f42b030b52747e7f5d0d6e04157e3843df68232ab1af3f8283b1d23943b',
    bundle_bytes=164433,bundle_sha256='13c0d9f6839971d10e598ca6718963146822e77ed913e89d536ffa541e01f441',
    nodes=108,root=107,target_ast_sha256='6a235e46d7ff57ccd23bfc381f5c48d024d739de8f78abded4fd58a37aea8dbd')
EXP_ARCHIVE=dict(case='CV070',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-scaled-exp-terms-v1/generation-process.json.gz',
    bytes=35768,sha256='ed605e26ac83f0ab130bf0406a80b7b1820db38b247ff86916bfcdb624f593d5',
    raw_bytes=668363,raw_sha256='2ed87385d786381359414f03049c26cf71327e987e60a3137683883a7b2370e4',
    bundle_bytes=381155,bundle_sha256='2be0d10e36a67786ed5fd20800f6a2d52c10229fea219ea68edd70e832a8b075',
    nodes=144,root=143,target_ast_sha256='7f9e9c6aa4b255463768b661ebe9736b133dd810525dfd27ff94dfbe3693bf1d')
ARCHIVES=(FIXED_ARCHIVE,ATANH_ARCHIVE,EXP_ARCHIVE,COMPOSITION_ARCHIVE,COMPARISON_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'fixed':FIXED_SOURCE,'atanh':ATANH_SOURCE,'exponential':EXP_SOURCE,
    'value_exists':'forall ab ac t H. exists y. NatHornerValue(ab,ac,t,H,y)',
    'power_exists':'forall a k. exists p. Pow(a,k,p)',
    'power_nonzero':'forall a. ~a=0 -> forall k p. Pow(a,k,p) -> ~p=0',
    'succ_nonzero':'forall a. ~S a=0','mul_nonzero':'forall a b. ~a=0 -> ~b=0 -> ~(a*b)=0'}
ENDPOINT_OWNERS=dict(fixed='AP085',atanh='CV025',exponential='CV070',value_exists='CV061',
    power_exists='AP010',power_nonzero='AP010',succ_nonzero='CV071',mul_nonzero='CV071')
HELPER_DEPENDENCIES={'AP086':tuple(ENDPOINT_SOURCES)}
INPUT_SNAPSHOT='research/arithmetic-library/sqrt2-power/observations/fixed-log-exp-witness-input-snapshot-v1.json'
INPUT_SNAPSHOT_BYTES=71401
INPUT_SNAPSHOT_SHA256='52690550d1b1405aa4e8748f15cd9798ef7e2cadc1bcc15b48a6a8c4d414a901'
INPUT_SOURCE_COUNT=302
INPUT_DEFINITION_COUNT=19


class FixedLogExpWitnessError(ValueError):
    """Changed constructed witness, uniform threshold or exact normalization."""


def recursive_definition_registry_for_audit():
    pool=dict(fixed_registry());identity=('stable_id','name','parameters','template_source','template_formula','conceptual_dependencies')
    for source in (coefficient_registry(),exp_registry()):
        for name,spec in source.items():
            if name in pool:
                if any(getattr(pool[name],key)!=getattr(spec,key) for key in identity):raise FixedLogExpWitnessError('shared fixed-witness definition changed')
            else:pool[name]=spec
    result={};visiting=set();ids=set()
    def visit(name):
        if name in result:return
        if name in visiting or name not in pool:raise FixedLogExpWitnessError('missing or cyclic fixed-witness definition')
        visiting.add(name);spec=pool[name]
        for dep in spec.conceptual_dependencies:visit(dep)
        if spec.stable_id in ids:raise FixedLogExpWitnessError('duplicate fixed-witness definition identity')
        result[name]=spec;ids.add(spec.stable_id);visiting.remove(name)
    for name in ('Le','NatAtanhPrefix','NatHornerValue','Pow','NatScaledExpRecurrence','Sum',
                 'NatZeroBefore','NatExpWeightTable','NatPowerWeightedPrefix','Factorial'):visit(name)
    return MappingProxyType(result)


def _input_snapshot():
    with (ROOT/INPUT_SNAPSHOT).open('rb') as stream:raw=stream.read(INPUT_SNAPSHOT_BYTES+1)
    if len(raw)!=INPUT_SNAPSHOT_BYTES or sha256(raw).hexdigest()!=INPUT_SNAPSHOT_SHA256:
        raise FixedLogExpWitnessError('fixed-witness exact input snapshot changed')
    value=json.loads(raw)
    if (value.get('schema')!='sqrt2-power-fixed-log-exp-witness-input-snapshot-v1'
            or value.get('authority')!='source_integrity_and_exact_definition_syntax_only_not_proof_authority'
            or len(value.get('definitions',[]))!=INPUT_DEFINITION_COUNT or len(value.get('source_pins',{}))!=INPUT_SOURCE_COUNT):
        raise FixedLogExpWitnessError('fixed-witness exact input snapshot envelope changed')
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
                or json_hash(encode_formula(spec.template_formula))!=digest):raise FixedLogExpWitnessError('fixed-witness conservative definition DAG changed')
        result[spec.name]=spec;ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_fixed_log_exp_witness_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=1 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise FixedLogExpWitnessError('AP086 exact fixed-schedule positive witness changed')
    return target


def source_contract():
    return dict(code='AP086',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,all_requested_precisions_including_zero=True,actual_precision_power='r=2^n',
        precision_chosen_before_arbitrary_later_index=True,sufficient_threshold='18*r+2<=k',
        actual_logarithm_and_exponential_computations_constructed=True,
        fixed_logarithm_prefix_length='2*k+1',fixed_exp_degree='k+2',
        positive_log_scale_argument_denominator_and_exp_head_proved=True,
        actual_factorial_and_denominator_power_constructed=True,head_factorization='h=(k+2)!*(d*p)^(k+2)',
        every_actual_term_factorial_normalization_retained=True,
        finite_upper_error='y/h<=2+2/r',finite_lower_error='2-1/r<=y/h',
        exact_definition_cone_reparsed_from_source_bound_snapshot=True,every_actual_source_rehashed=True,
        new_induction_count=0,new_induction_needed=False,new_solver_arithmetic_leaf_needed=False,
        new_definition_ids=[],definition_admissions=0,root_quotient_accuracy_claimed=False,
        analytic_log_exp_identity_claimed=False,analytic_limit_claimed=False,fixed_approximation_program_changed=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def recursive_source_pins_for_audit():
    result=fixed_log_exp_convergence_source_pins()
    for source in (atanh_coefficients_source_pins,scaled_exp_terms_source_pins):
        for name,pin in source().items():
            if name in result and result[name]!=pin:raise FixedLogExpWitnessError('fixed-witness dependency source disagreement')
            result[name]=pin
    expected={'scripts/sqrt2_power_fixed_log_exp_convergence.py':'43c5a5177b5bc7aeb282d1b2c6523297b1b18281d1e3d2bc13d1e34b8d82bb72',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in ('scripts/sqrt2_power_atanh_coefficients.py','scripts/sqrt2_power_scaled_exp_terms.py',
                 'scripts/sqrt2_power_log_exp_uniform_two.py','scripts/sqrt2_power_mixed_assembly.py'):
        if name not in result:raise FixedLogExpWitnessError('unbound fixed-witness constructor: '+name)
    for name in (*expected,'scripts/sqrt2_power_fixed_log_exp_witness.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:raise FixedLogExpWitnessError('fixed-witness source or archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def fixed_log_exp_witness_source_pins():
    expected=_input_snapshot()['source_pins'];result={INPUT_SNAPSHOT:dict(bytes=INPUT_SNAPSHOT_BYTES,sha256=INPUT_SNAPSHOT_SHA256)}
    for name in (*expected,'scripts/sqrt2_power_fixed_log_exp_witness.py'):
        if name.startswith('/') or '..' in name.split('/'):raise FixedLogExpWitnessError('fixed-witness source path escaped repository')
        bound=expected[name]['bytes'] if name in expected else 2*1024**2;digest=sha256();size=0
        with (ROOT/name).open('rb') as stream:
            while size<=bound:
                chunk=stream.read(min(65536,bound+1-size))
                if not chunk:break
                size+=len(chunk);digest.update(chunk)
        actual=dict(bytes=size,sha256=digest.hexdigest())
        if size>bound or name in expected and actual!=expected[name]:raise FixedLogExpWitnessError('fixed-witness source bytes changed')
        result[name]=actual
    return result


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.terms import Mul,Succ,parse_term
    two,three=map(parse_term,('2','3'))
    def exponential(t):
        k,d,ab,ac,x,p,tb,tc,h,y=t.terms(('k','d','ab','ac','x','p','tb','tc','h','y'))
        coefficients=t.hyp('coefficient_data');data=t.hyp('exp_data')
        bounds=apply(instantiate(field(t.hyp('fixed_data'),2,3),k,d,ab,ac,x,p,tb,tc,h,y),
            t.hyp('threshold'),field(coefficients,0,3),field(coefficients,1,3),t.hyp('value'),t.hyp('power'),
            field(data,9,11),field(data,3,11),field(data,8,11))
        result=conjunction(field(coefficients,0,3),field(coefficients,1,3),t.hyp('value'),t.hyp('power'),
            field(bounds,0,4),field(bounds,1,4),*(field(data,i,11) for i in range(11)),field(bounds,2,4),field(bounds,3,4))
        return witness(t.terms(OUTPUTS),result)
    def powered(t):
        d,p,x,k=t.terms(('d','p','x','k'));length=Succ(Mul(two,k))
        pnz=apply(instantiate(apply(specialize(t,'power_nonzero',three),specialize(t,'succ_nonzero',two)),length,p),t.hyp('power'))
        positive=apply(specialize(t,'mul_nonzero',d,p),field(t.hyp('coefficient_data'),0,3),pnz)
        actual=apply(specialize(t,'exponential',Mul(d,p),Mul(three,x),Succ(Succ(k))),positive)
        return eliminate(t,actual,EXP_OUTPUTS,'exp_data',exponential)
    def valued(t):
        return eliminate(t,specialize(t,'power_exists',three,Succ(Mul(two,t.term('k')))),('p',),'power',powered)
    def coefficients(t):
        return eliminate(t,specialize(t,'value_exists',*t.terms(('ab','ac')),three,Succ(Mul(two,t.term('k')))),('x',),'value',valued)
    def later(t):
        return eliminate(t,specialize(t,'atanh',Succ(Mul(two,t.term('k')))),('d','ab','ac'),'coefficient_data',coefficients)
    def precision(t):
        universal=introduce(t,('k',),('threshold',),later)
        return witness((t.term('r'),),conjunction(field(t.hyp('fixed_data'),0,3),field(t.hyp('fixed_data'),1,3),universal))
    return introduce(s,('n',),(),lambda t:eliminate(t,specialize(t,'fixed',t.term('n')),('r',),'fixed_data',precision))


def prove_fixed_log_exp_witness(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP086',target=frozen_fixed_log_exp_witness_target(_registry=registry),registry=registry,
        helper_sources={},helper_hashes={},endpoint_sources=ENDPOINT_SOURCES,endpoint_owners=ENDPOINT_OWNERS,
        archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories={'AP086':_root},pins=fixed_log_exp_witness_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
