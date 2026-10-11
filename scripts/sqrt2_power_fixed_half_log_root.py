"""AP090: fixed-schedule half-log samples compared with one actual dyadic root.

Reuse the exact AP085 index identities and AP007 gap witness. Retain the
original independent computations and AP089's quantifier order. No new
arithmetic helper, definition, analytic identity or acceptance shortcut.
"""
from hashlib import sha256
import json

from sqrt2_power_half_log_root_uniform import (
    ROOT,Scope,introduce,eliminate,witness,apply,specialize,conjunction,field,canonical,json_hash,
    definition_registry,half_log_root_uniform_source_pins,NAMED_SOURCE as UNIFORM_SOURCE,
    FINE_CONCLUSION as CONCLUSION,
)
from sqrt2_power_fixed_log_exp_convergence import (
    HELPER_SOURCES as INDEX_SOURCES,HELPER_TARGET_SHA256 as INDEX_HASHES,
    fixed_log_exp_convergence_source_pins,ORDER_ARCHIVE,
)
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-fixed-half-log-root-v1'
PARAMETERS=('k','e','bb','bc','z','q','eb','ec','b','v')
PREMISES=('Le(S(S(18*r)),k)','~e=0','NatAtanhPrefix(e,bb,bc,S(2*k))',
    'NatHornerValue(bb,bc,3,S(2*k),z)','Pow(3,S(2*k),q)',
    'NatScaledExpRecurrence(2*(e*q),3*z,eb,ec,S(S k))','BetaAt(eb,ec,0,b)','Sum(eb,ec,S(S(S k)),v)')
LATER_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> '+CONCLUSION
NAMED_SOURCE='forall n. exists r s. Pow(2,n,r) /\\ (~r=0 /\\ (DyadicSqrt2(n,r,s) /\\ ('+LATER_SOURCE+')))'
TARGET_SHA256='41651cb7c7afc07ceb0eaeab7bf02392001a704ec0891d7bf1db0ed4aa33211f'
INDEX_PAIR='S(2*k)=(S(S(18*r)))+S(k+offset) /\\ S(S k)=(S(S(S(18*r))))+(S offset)'
UNIFORM_ARCHIVE=dict(case='AP089',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-half-log-root-uniform-v3/generation-process.json.gz',
    bytes=238087,sha256='a64427553bd5ed792c5311db3ccdda60c787aaeecd3a8abee040ac8f014c113e',
    raw_bytes=6279699,raw_sha256='3d44e43cc1d64c2a5e1c85538c57837d602e76025fb838e7092f5364cc05ad84',
    bundle_bytes=3848765,bundle_sha256='40a9356ff0ed241d51a10a9948e73f850ff7b8cd979cb9ca1531a692fa238b49',
    nodes=583,root=582,target_ast_sha256='bdd05acec456f38c8dbd660093564668cdcb6a6207fd285396940740dcf42ff8')
INDEX_ARCHIVE=dict(case='AP085',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-log-exp-convergence-v1/generation-process.json.gz',
    bytes=206369,sha256='966014b2b7f9fe91417d0007c65e8af332463e1043cb515f45f664541bf83d5e',
    raw_bytes=5432179,raw_sha256='43924032fc3a0a1f7716cc29500bd8f208c80352c606d137577e35a04eea75c7',
    bundle_bytes=3330729,bundle_sha256='68e17a66cae013163f697f1a85a48dc2d9a05b8f84a2c621b5a3ca15547cf2a7',
    nodes=513,root=512,target_ast_sha256='c49cb9e52773c0bae1157f7b1eedbc0f29391c3163cb80a3c9c28445c69c37b1')
ARCHIVES=(UNIFORM_ARCHIVE,INDEX_ARCHIVE,ORDER_ARCHIVE)
ENDPOINT_SOURCES={'uniform':UNIFORM_SOURCE,'le_gap':'forall a b. Le(a,b) -> exists g. b=a+g','indices':INDEX_SOURCES['indices']}
ENDPOINT_OWNERS=dict(uniform='AP089',le_gap='AP007',indices='AP085')
HELPER_SOURCES={}
HELPER_TARGET_SHA256={}
HELPER_DEPENDENCIES={'AP090':tuple(ENDPOINT_SOURCES)}
SOURCE_SNAPSHOT='research/arithmetic-library/sqrt2-power/observations/fixed-half-log-root-source-snapshot-v1.json'
SOURCE_SNAPSHOT_BYTES=61329
SOURCE_SNAPSHOT_SHA256='580a983caa7d2d9a1233a82dfa533ceabb2e6e7613fbbe3afefbebb35bdbf374'
INHERITED_SOURCE_COUNT=362


class FixedHalfLogRootError(ValueError):
    """Changed root, actual fixed schedule, source closure or finite errors."""


def frozen_fixed_half_log_root_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if (binders!=1 or premises or type(conclusion) is not Exists or type(conclusion.body) is not Exists
            or json_hash(encode_formula(target))!=TARGET_SHA256):
        raise FixedHalfLogRootError('AP090 exact fixed half-log/root target changed')
    return target


def source_contract():
    return dict(code='AP090',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,all_requested_precisions_including_zero=True,actual_precision_power='r=2^n',
        actual_root_chosen_before_all_later_computations=True,root_computation_retained='DyadicSqrt2(n,r,s)',
        coefficient_scale_positive_required=True,supplied_computation_and_codes_preserved=True,
        fixed_logarithm_prefix_length='2*k+1',fixed_exp_degree='k+2',sufficient_threshold='18*r+2<=k',
        actual_cutoff_gap_constructed=True,logarithm_horizon_alignment='2*k+1=M+(k+t+1) when k=M+t',
        exponential_horizon_alignment='k+2=(M+1)+(t+1) when k=M+t',
        actual_power_and_doubled_argument_denominator_proved_nonzero=True,original_logarithm_coefficient_scale_retained=True,
        finite_cross_bounds=['r*v<=s*b+8*b','s*b<=r*v+b'],finite_rational_error='-1/r<=v/b-s/r<=8/r',
        rational_reading_requires_positive_fine_head=True,zero_fine_head_allowed=True,
        archived_indices_helper=dict(case='AP085',statement_ast_sha256=INDEX_HASHES['indices']),
        new_solver_arithmetic_leaf_needed=False,new_induction_count=0,new_induction_needed=False,
        new_definition_ids=[],definition_admissions=0,existing_checked_cut_nodes_introduced=1,
        sharing_scope='one_instantiated_pair_of_checked_index_equalities_in_the_new_root',
        root_quotient_accuracy_claimed=False,analytic_half_log_sqrt2_identity_claimed=False,analytic_limit_claimed=False,
        fixed_approximation_program_changed=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def recursive_source_pins_for_audit():
    result=half_log_root_uniform_source_pins()
    for name,pin in fixed_log_exp_convergence_source_pins().items():
        if name in result and result[name]!=pin:raise FixedHalfLogRootError('fixed half-log/root source disagreement')
        result[name]=pin
    expected={'scripts/sqrt2_power_half_log_root_uniform.py':'bcda5f0d1da8df82a180bdf6b69751fd2e03e81e6bf7dd1aabeb7b74b4961feb',
        'scripts/sqrt2_power_fixed_log_exp_convergence.py':'43c5a5177b5bc7aeb282d1b2c6523297b1b18281d1e3d2bc13d1e34b8d82bb72',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in ('scripts/sqrt2_power_convolution_unit.py','scripts/sqrt2_power_mixed_assembly.py'):
        if name not in result:raise FixedHalfLogRootError('unbound fixed half-log/root constructor')
    for name in (*expected,'scripts/sqrt2_power_fixed_half_log_root.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise FixedHalfLogRootError('fixed half-log/root source or archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _source_snapshot():
    with (ROOT/SOURCE_SNAPSHOT).open('rb') as stream:raw=stream.read(SOURCE_SNAPSHOT_BYTES+1)
    if len(raw)!=SOURCE_SNAPSHOT_BYTES or sha256(raw).hexdigest()!=SOURCE_SNAPSHOT_SHA256:
        raise FixedHalfLogRootError('fixed half-log/root source snapshot changed')
    value=json.loads(raw)
    if (value.get('schema')!='sqrt2-power-fixed-half-log-root-source-snapshot-v1'
            or value.get('authority')!='source_integrity_only_not_proof_authority'
            or len(value.get('source_pins',{}))!=INHERITED_SOURCE_COUNT):
        raise FixedHalfLogRootError('fixed half-log/root source snapshot envelope changed')
    return value


def fixed_half_log_root_source_pins():
    expected=_source_snapshot()['source_pins']
    result={SOURCE_SNAPSHOT:dict(bytes=SOURCE_SNAPSHOT_BYTES,sha256=SOURCE_SNAPSHOT_SHA256)}
    for name in (*expected,'scripts/sqrt2_power_fixed_half_log_root.py'):
        if name.startswith('/') or '..' in name.split('/'):raise FixedHalfLogRootError('fixed half-log/root source path escaped')
        bound=expected[name]['bytes'] if name in expected else 2*1024**2;digest=sha256();size=0
        with (ROOT/name).open('rb') as stream:
            while size<=bound:
                chunk=stream.read(min(65536,bound+1-size))
                if not chunk:break
                size+=len(chunk);digest.update(chunk)
        actual=dict(bytes=size,sha256=digest.hexdigest())
        if size>bound or name in expected and actual!=expected[name]:raise FixedHalfLogRootError('fixed half-log/root source bytes changed')
        result[name]=actual
    return result


def _root(scope,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.proofs import CongS,Cut
    from peano_lab.kernel.terms import Add,Mul,Succ,parse_term
    eighteen=parse_term('18')
    def aligned(t):
        k,e,bb,bc,z,q,eb,ec,b,v=t.terms(PARAMETERS);offset=t.term('offset')
        lengths=t.hyp('index_data');log=field(lengths,0,2);exp=field(lengths,1,2)
        prefix=_subst(t,registry,'NatAtanhPrefix(e,bb,bc,slot)',log,t.hyp('prefix'))
        value=_subst(t,registry,'NatHornerValue(bb,bc,3,slot,z)',log,t.hyp('value'))
        power=_subst(t,registry,'Pow(3,slot,q)',log,t.hyp('power'))
        terms=_subst(t,registry,'NatScaledExpRecurrence(2*(e*q),3*z,eb,ec,slot)',exp,t.hyp('terms'))
        total=_subst(t,registry,'Sum(eb,ec,slot,v)',CongS(exp),t.hyp('total'))
        universal=field(t.hyp('uniform_data'),3,4)
        return apply(instantiate(universal,e,bb,bc,Succ(Add(k,offset)),z,q,Succ(offset),eb,ec,b,v),
            t.hyp('nonzero'),prefix,value,power,terms,t.hyp('head'),total)
    def chosen(t):
        M=Succ(Succ(Mul(eighteen,t.term('r'))))
        lengths=apply(specialize(t,'indices',M,t.term('offset'),t.term('k')),t.hyp('gap'))
        return Cut(parse_named(INDEX_PAIR,t.variables,registry),parse_named(CONCLUSION,t.variables,registry),
            lengths,aligned(t.hypothesis('index_data')))
    def later(t):
        M=Succ(Succ(Mul(eighteen,t.term('r'))))
        gap=apply(specialize(t,'le_gap',M,t.term('k')),t.hyp('threshold'))
        return eliminate(t,gap,('offset',),'gap',chosen)
    def precision(t):
        data=t.hyp('uniform_data')
        universal=introduce(t,PARAMETERS,('threshold','nonzero','prefix','value','power','terms','head','total'),later)
        return witness(t.terms(('r','s')),conjunction(field(data,0,4),field(data,1,4),field(data,2,4),universal))
    return introduce(scope,('n',),(),lambda t:eliminate(t,specialize(t,'uniform',t.term('n')),('r','s'),'uniform_data',precision))


def prove_fixed_half_log_root(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP090',target=frozen_fixed_half_log_root_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'AP090':lambda s:_root(s,registry)},pins=fixed_half_log_root_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
