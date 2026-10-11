"""AP050: construct actual finite half-log and dyadic-root witnesses together.

Retain all AP047 computation and square-error fields, construct the actual
floor root at the same r=2^n, and prove both natural cross-product errors.
This is an all-precision finite bridge, not an infinite analytic identity.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_half_log_square import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,conjoin,definition_registry as half_registry,
    OUTPUTS as HALF_OUTPUTS,PARTS as HALF_PARTS,NAMED_SOURCE as HALF_SOURCE,
)
from sqrt2_power_half_log_root_comparison import (
    NAMED_SOURCE as COMPARISON_SOURCE,half_log_root_comparison_source_pins,BOUND_ARCHIVE,
)
from sqrt2_power_dyadic_sqrt2 import definition_registry as dyadic_registry
from sqrt2_power_dyadic_sqrt2_square_error import NAMED_SOURCE as SQUARE_SOURCE
from sqrt2_power_dyadic_sqrt2_reciprocal import SQUARE_ARCHIVE
from sqrt2_power_floor_sqrt_comparison import FLOOR_ARCHIVE
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-half-log-root-witness-v1'
OUTPUTS=HALF_OUTPUTS+('s',)
ROOT_PARTS=('DyadicSqrt2(n,r,s)','Le(r*(u*r),r*(s*h)+7*(h*r))','Le(r*(s*h),r*(u*r)+(h*r))')
PARTS=HALF_PARTS+ROOT_PARTS
NAMED_SOURCE='forall n. exists '+' '.join(OUTPUTS)+'. '+conjoin(PARTS)
TARGET_SHA256='4110740f69dfccac4fd2f8dfa027de161e05948d42f010fe33bdf3b03c1bcbca'
HELPER_SOURCES={}
HELPER_TARGET_SHA256={}
HALF_ARCHIVE=dict(case='AP047',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-half-log-square-v2/generation-process.json.gz',
    bytes=211943,sha256='3482795be1de1f50b8e6de29b1ce49b672f47c4dc044b8a251d957a3a4c65d31',
    raw_bytes=5553397,raw_sha256='a5a9f839875011ae9cc67de2f079b8bd0d4f0c66f346dd350eebd2c41e3800c5',
    bundle_bytes=3394200,bundle_sha256='bcfc3286e107e3bdd1183f92793abd07c53a65c28f685c9f8f147cde6b08dc08',
    nodes=535,root=534,target_ast_sha256='b66c87c593359c085b44249ad7621de4058ef1ab24fbba8de8d70e15ef26af40')
COMPARISON_ARCHIVE=dict(case='AP049',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-half-log-root-comparison-v1/generation-process.json.gz',
    bytes=47337,sha256='8610868ac1ae296df5d28f124fec9785661cacfeb4c5edab26a200face1b49ee',
    raw_bytes=291758,raw_sha256='33e23ff8c747fecdc320b9e2e13515cc71822c9d67a6fc5052f01cb1ba0bf74e',
    bundle_bytes=105365,bundle_sha256='04b9f79d32692a6e9a82255c8dc6f5f969d9e7b7ebe1b4776e22906e159a5f3a',
    nodes=38,root=37,target_ast_sha256='ca484cb2209e8e2ed81d29e1903feb31e830a531b0e621cf00ce722956568c9b')
ARCHIVES=(HALF_ARCHIVE,COMPARISON_ARCHIVE,SQUARE_ARCHIVE,FLOOR_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'half':HALF_SOURCE,'comparison':COMPARISON_SOURCE,'square':SQUARE_SOURCE,
    'floor_exists':'forall n. exists s. FloorSqrt(n,s)','le_refl':'forall a. Le(a,a)'}
ENDPOINT_OWNERS=dict(half='AP047',comparison='AP049',square='SQ009',floor_exists='SQ001',le_refl='CV071')
HELPER_DEPENDENCIES={'AP050':tuple(ENDPOINT_SOURCES)}


class HalfLogRootWitnessError(ValueError):
    """Changed actual witness construction, exact graph or finite error."""


def definition_registry():
    result=dict(half_registry());roots=dyadic_registry()
    for name,spec in roots.items():
        if name in result:
            old=result[name]
            if (old.stable_id,old.parameters,old.template_formula,old.conceptual_dependencies)!=(
                    spec.stable_id,spec.parameters,spec.template_formula,spec.conceptual_dependencies):
                raise HalfLogRootWitnessError('shared conservative root definition changed')
        else:
            if not set(spec.conceptual_dependencies)<=result.keys() or spec.stable_id in {d.stable_id for d in result.values()}:
                raise HalfLogRootWitnessError('root definition dependency or identity changed')
            result[name]=spec
    return MappingProxyType(result)


def frozen_half_log_root_witness_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=1 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise HalfLogRootWitnessError('AP050 exact actual half-log and root witness changed')
    return target


def source_contract():
    return dict(code='AP050',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,all_precisions_including_zero=True,actual_r_equals_two_to_n=True,
        actual_half_log_and_same_precision_dyadic_root_constructed=True,
        all_AP047_computation_and_square_error_fields_retained=True,
        proved_positive_scales=['r','d','q','d*q','h'],
        finite_cross_error='r*u*r<=r*s*h+7*h*r; r*s*h<=r*u*r+h*r',
        rational_reading='-1/r<=u/h-s/r<=7/r',
        fixed_approximation_program_changed=False,large_ground_power_materialized=False,
        new_induction_needed=False,new_induction_count=0,new_definition_ids=[],definition_admissions=0,
        analytic_half_log_sqrt2_identity=False,analytic_limit_claim=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def half_log_root_witness_source_pins():
    result=half_log_root_comparison_source_pins()
    expected={'scripts/sqrt2_power_half_log_root_comparison.py':'b478179b274b9f2d86f1a78c59782c36d3ed185b7194504a3e7c275205584476',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_half_log_root_witness.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise HalfLogRootWitnessError('finite half-log root source or archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _root(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Mul,parse_term
    def rooted(t):
        n,r,u,h,root=t.terms(('n','r','u','h','s'));old=t.hyp('half_data')
        graph=conjunction(field(old,0,22),t.hyp('floor'))
        square=apply(specialize(t,'square',n,r,root),graph)
        error=apply(specialize(t,'comparison',r,u,h,root,r),field(old,9,22),field(old,1,22),
            specialize(t,'le_refl',r),field(square,2,6),field(square,4,6),field(square,5,6),field(old,20,22),field(old,21,22))
        return witness(t.terms(OUTPUTS),conjunction(*(field(old,i,22) for i in range(22)),
            graph,AndElimL(error),AndElimR(error)))
    def chosen(t):
        r=t.term('r')
        return eliminate(t,specialize(t,'floor_exists',Mul(parse_term('2'),Mul(r,r))),('s',),'floor',rooted)
    return introduce(s,('n',),(),lambda t:eliminate(t,specialize(t,'half',t.term('n')),HALF_OUTPUTS,'half_data',chosen))


def prove_half_log_root_witness(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP050',target=frozen_half_log_root_witness_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'AP050':_root},pins=half_log_root_witness_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
