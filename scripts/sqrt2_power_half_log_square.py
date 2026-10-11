"""AP047: construct an actual half-logarithm exponential with square near two.

At r=2^n and M=18*r+2, retain the exact atanh/Horner argument and all
factorial-weighted half-argument computations. The short sum u/h satisfies
2-1/r <= (u/h)^2 <= 2+3/r, expressed only by natural cross products.
Neither sqrt(2) identification nor an infinite exponential law is assumed.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_log_exp_dyadic_witness import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,conjoin,definition_registry as source_registry,
    NAMED_SOURCE as LOG_SOURCE,log_exp_dyadic_witness_source_pins,COMPARISON_ARCHIVE,
)
from sqrt2_power_exp_half_square import NAMED_SOURCE as HALF_SOURCE,exp_half_square_source_pins
from sqrt2_power_half_square_error_transfer import NAMED_SOURCE as ERROR_SOURCE
from sqrt2_power_half_log_precision import NAMED_SOURCE as PRECISION_SOURCE,half_log_precision_source_pins
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-half-log-square-v1'
M='S(S(18*r))'
H=f'(S({M}))+({M})'
LOG_OUTPUTS=('r','d','lb','lc','x','q','eb','ec','b','v')
HALF_OUTPUTS=('wb','wc','ab','ac','h','f','t','z','u')
OUTPUTS=LOG_OUTPUTS[:6]+HALF_OUTPUTS
LOG_PARTS=('Pow(2,n,r)','~r=0','~d=0',f'NatAtanhPrefix(d,lb,lc,{M})',
    f'NatHornerValue(lb,lc,3,{M},x)',f'Pow(3,{M},q)','~q=0','~(d*q)=0','Le(3*x,d*q)')
HALF_PARTS=('~h=0',f'NatExpWeightTable(2*(d*q),{H},wb,wc)',
    f'NatPowerWeightedPrefix(3*x,wb,wc,ab,ac,S({H}))','BetaAt(wb,wc,0,h)','BetaAt(ab,ac,0,h)',
    f'Factorial({H},f)',f'Pow(2*(d*q),{H},t)','h=f*t',f'Sum(ab,ac,S({H}),z)',
    f'NatScaledExpRecurrence(2*(d*q),3*x,ab,ac,{H})',f'Sum(ab,ac,S({M}),u)')
ERROR_PARTS=('Le(r*(u*u),(r*2)*(h*h)+3*(h*h))','Le((r*2)*(h*h),r*(u*u)+(h*h))')
PARTS=LOG_PARTS+HALF_PARTS+ERROR_PARTS
NAMED_SOURCE='forall n. exists '+' '.join(OUTPUTS)+'. '+conjoin(PARTS)
TARGET_SHA256='b66c87c593359c085b44249ad7621de4058ef1ab24fbba8de8d70e15ef26af40'
HELPER_SOURCES={}
HELPER_TARGET_SHA256={}
LOG_ARCHIVE=dict(case='AP034',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-log-exp-dyadic-witness-v1/generation-process.json.gz',
    bytes=176621,sha256='e7beb111df48afd373d27ee9f6f35167930459c527517e13aba3ceb3145d33f2',
    raw_bytes=4600191,raw_sha256='bf695db3a3c890caff7f3a0354b449a787708b902bcc70907b6c7a89b9392cb2',
    bundle_bytes=2812849,bundle_sha256='99ef8cd7a0cdd76a9c39d828620e1c8858565b70d202b79dfb36df034bddb63e',
    nodes=452,root=451,target_ast_sha256='c7f28f686ec9b7eb26f152b6aed3eecb9aa4b32a686ba022e3ba80d363e5f620')
HALF_ARCHIVE=dict(case='AP044',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-half-square-v1/generation-process.json.gz',
    bytes=109883,sha256='b9c8507c33ba99903df93523a024c9952208eadb44c072e61522c67196494406',
    raw_bytes=2288975,raw_sha256='a27f22d9cb9a7b2690d243a803cd5e40d7514ddbe24f804df49f65ae8a9a3c2a',
    bundle_bytes=1357563,bundle_sha256='f65fd8094f9b078f62b6ee80b550b4bb62cff1c7a7728edc179d6215ae3fb413',
    nodes=303,root=302,target_ast_sha256='a0ae3b4a0d82774e120a7703228bf12483ea7f606b04303d09fac179c58075e7')
ERROR_ARCHIVE=dict(case='AP045',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-half-square-error-transfer-v1/generation-process.json.gz',
    bytes=41984,sha256='41ce4163cf807c9b9a155015f05a5f1731e88b1c751a0b497a58e45403a9a822',
    raw_bytes=197333,raw_sha256='d9a025aecf4002f8e5142f2b7a36fffcb9742c1459a6d8429549fc0232ab74be',
    bundle_bytes=49023,bundle_sha256='7291b21a18f894888444ab9878c95369fecca20d89d7797c733d11b451fd8d09',
    nodes=28,root=27,target_ast_sha256='3d7f11a02582d2bf7b63377cc8ec2bbabf74c584db7e7e1f5627256c208e7c84')
PRECISION_ARCHIVE=dict(case='AP046',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-half-log-precision-v1/generation-process.json.gz',
    bytes=33965,sha256='a8aa5cf416eba42d7ac60677297def6b0b582b83effc747df788f37f1425a8cd',
    raw_bytes=213916,raw_sha256='1ced030dc8e04ad27296497367bd7f66e58f7d7cf2c99b2dd65ae63a28613f4a',
    bundle_bytes=78373,bundle_sha256='96815002d9cbada491bb67202df76d032ac56ed7b8f0c85b32d92a1406e3368a',
    nodes=37,root=36,target_ast_sha256='936a988b2a6fae61ebb3206a2a33746d5c8ad2e23501f642b0528b6b9e0e7877')
ARCHIVES=(LOG_ARCHIVE,HALF_ARCHIVE,ERROR_ARCHIVE,PRECISION_ARCHIVE,COMPARISON_ARCHIVE)
ENDPOINT_SOURCES={'log_witness':LOG_SOURCE,'half_square':HALF_SOURCE,'error_transfer':ERROR_SOURCE,
    'precision':PRECISION_SOURCE,'power_exists':'forall a k. exists p. Pow(a,k,p)'}
ENDPOINT_OWNERS=dict(log_witness='AP034',half_square='AP044',error_transfer='AP045',precision='AP046',power_exists='AP010')
HELPER_DEPENDENCIES={'AP047':tuple(ENDPOINT_SOURCES)}
INPUT_SNAPSHOT='research/arithmetic-library/sqrt2-power/observations/half-log-square-input-snapshot-v1.json'
INPUT_SNAPSHOT_BYTES=75931
INPUT_SNAPSHOT_SHA256='ef70a1ba1a64af8df00d17df9022c3d01eabc0b0bae0d803f067c3ae291d5180'


class HalfLogSquareError(ValueError):
    """Changed actual logarithm/half-exponential construction or square bound."""


def _input_snapshot():
    with (ROOT/INPUT_SNAPSHOT).open('rb') as stream: raw=stream.read(INPUT_SNAPSHOT_BYTES+1)
    if len(raw)!=INPUT_SNAPSHOT_BYTES or sha256(raw).hexdigest()!=INPUT_SNAPSHOT_SHA256:
        raise HalfLogSquareError('exact input syntax/source snapshot changed')
    value=json.loads(raw)
    if (value.get('schema')!='sqrt2-power-half-log-square-input-snapshot-v1'
            or value.get('authority')!='source_integrity_and_exact_definition_syntax_only_not_proof_authority'
            or len(value.get('definitions',[]))!=17 or len(value.get('source_pins',{}))!=335):
        raise HalfLogSquareError('exact input syntax/source snapshot envelope changed')
    return value


def definition_registry():
    """Reparse only the exact existing cone, not unrelated ancestor notation.

    The snapshot is syntax, never a proof receipt. Each expanded template is
    reparsed by the unchanged hygienic constructor and checked against its
    frozen AST. Regression compares every DefinitionSpec to the old producer.
    """
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
            raise HalfLogSquareError('existing logarithm/half-exponential definition DAG changed')
        result[spec.name]=spec;ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_half_log_square_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=1 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise HalfLogSquareError('AP047 exact actual half-logarithm square witness changed')
    return target


def source_contract():
    return dict(code='AP047',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,all_precisions_including_zero=True,actual_precision_power='r=2^n',
        logarithm_degree='M=18*r+2',half_exponential_degree='2*M+1',half_short_sum_degree='M',
        half_argument='3*x/(2*(d*q))',actual_logarithm_and_half_exponential_computations_constructed=True,
        proved_positive_scales=['r','d','q','d*q','h'],
        finite_square_error='2-1/r<=(u/h)^2<=2+3/r',only_natural_cross_products_asserted=True,
        auxiliary_comparison_witnesses_internal_but_all_proof_bodies_retained=True,
        exact_definition_cone_reparsed_from_source_bound_snapshot=True,
        every_actual_source_rehashed_without_recursive_duplicate_reads=True,
        fixed_approximation_program_changed=False,large_ground_power_materialized=False,
        new_induction_needed=False,new_induction_count=0,new_definition_ids=[],definition_admissions=0,
        sqrt2_identification=False,analytic_exponential_identity=False,analytic_limit_claim=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def recursive_source_pins_for_audit():
    """Independent old closure construction; workers stream each file once."""
    result=exp_half_square_source_pins()
    for source in (log_exp_dyadic_witness_source_pins(),half_log_precision_source_pins()):
        for name,pin in source.items():
            if name in result and result[name]!=pin:
                raise HalfLogSquareError('half-log square ancestor source disagreement')
            result[name]=pin
    expected={'scripts/sqrt2_power_log_exp_dyadic_witness.py':'1545cf9e78a6f62f355e7a35fb46f88222d3bd35ace4f99bfec43a74cdf8d883',
        'scripts/sqrt2_power_exp_half_square.py':'d3a21dde4868b76906976cd9c417915907148754ad3f2ee5468867d64cdb7218',
        'scripts/sqrt2_power_half_square_error_transfer.py':'b7e2f4e8157408813f4ebd2665932a0efbd5b05f0369ceab0a91ba3c37878d49',
        'scripts/sqrt2_power_half_log_precision.py':'a009a1c8acc576cc5c2a244580c239aa2d82b799590b3c777b8ca77e245f7579',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_half_log_square.py'):
        with (ROOT/name).open('rb') as stream: raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise HalfLogSquareError('half-log square source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def half_log_square_source_pins():
    expected=_input_snapshot()['source_pins']
    result={INPUT_SNAPSHOT:dict(bytes=INPUT_SNAPSHOT_BYTES,sha256=INPUT_SNAPSHOT_SHA256)}
    for name in (*expected,'scripts/sqrt2_power_half_log_square.py'):
        if name.startswith('/') or '..' in name.split('/'):
            raise HalfLogSquareError('half-log square source path escaped repository')
        bound=expected[name]['bytes'] if name in expected else 2*1024**2
        digest=sha256();size=0
        with (ROOT/name).open('rb') as stream:
            while size<=bound:
                chunk=stream.read(min(65536,bound+1-size))
                if not chunk: break
                size+=len(chunk);digest.update(chunk)
        actual=dict(bytes=size,sha256=digest.hexdigest())
        if size>bound or name in expected and actual!=expected[name]:
            raise HalfLogSquareError('half-log square source or actual archive changed')
        result[name]=actual
    return result


def _root(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Mul,Succ,parse_term
    def chosen(t):
        old=t.hyp('log_data');half=t.hyp('half_data');r,p,b,h,u,v=t.terms(('r','p','b','h','u','v'))
        precision=apply(specialize(t,'precision',r,p),t.hyp('power'))
        bounds=apply(specialize(t,'error_transfer',r,p,b,Mul(h,h),Mul(u,u),v),
            field(old,7,15),AndElimL(precision),AndElimR(precision),field(half,11,13),field(half,12,13),field(old,13,15),field(old,14,15))
        return witness(t.terms(OUTPUTS),conjunction(*(field(old,i,15) for i in (0,1,2,3,4,5,6,8,9)),
            *(field(half,i,13) for i in range(11)),AndElimL(bounds),AndElimR(bounds)))
    def powered(t):
        d,x,q,r,b,v,p=t.terms(('d','x','q','r','b','v','p'));M=Succ(Succ(Mul(parse_term('18'),r)));old=t.hyp('log_data')
        data=apply(specialize(t,'half_square',Mul(d,q),Mul(parse_term('3'),x),*t.terms(('eb','ec')),M,b,v,p),
            field(old,8,15),field(old,9,15),field(old,10,15),field(old,11,15),field(old,12,15),t.hyp('power'))
        return eliminate(t,data,HALF_OUTPUTS,'half_data',chosen)
    def logged(t):
        M=Succ(Succ(Mul(parse_term('18'),t.term('r'))))
        return eliminate(t,specialize(t,'power_exists',parse_term('2'),M),('p',),'power',powered)
    return introduce(s,('n',),(),lambda t:eliminate(t,specialize(t,'log_witness',t.term('n')),LOG_OUTPUTS,'log_data',logged))


def prove_half_log_square(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP047',target=frozen_half_log_square_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'AP047':_root},pins=half_log_square_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
