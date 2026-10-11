"""AP088: prove the actual cutoff budgets for half-logarithm refinement.

AP087 supplies the explicitly halved arguments. Reuse AP083's checked power
budgets, positive cancellation and proof constructor with their exact inputs.
"""
from hashlib import sha256

from sqrt2_power_half_log_exp_refinement import (
    ROOT,Scope,introduce,canonical,json_hash,definition_registry,
    NAMED_SOURCE as REFINEMENT_SOURCE,half_log_exp_refinement_source_pins,
)
from sqrt2_power_log_exp_cutoff_refinement import (
    M,PARAMETERS,PREMISES as FULL_PREMISES,CONCLUSION as FULL_CONCLUSION,
    HELPER_SOURCES as BUDGET_SOURCES,log_exp_cutoff_refinement_source_pins,_root,
)
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-half-log-exp-cutoff-v1'
PREMISES=tuple(p.replace('NatScaledExpRecurrence(d*p,','NatScaledExpRecurrence(2*(d*p),')
    .replace('NatScaledExpRecurrence(e*q,','NatScaledExpRecurrence(2*(e*q),') for p in FULL_PREMISES)
CONCLUSION=FULL_CONCLUSION.replace('~(d*p)=0','~(2*(d*p))=0').replace('~(e*q)=0','~(2*(e*q))=0')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> '+CONCLUSION
TARGET_SHA256='da6645f80e599d951709a835b4f07996fb457ad7c848fe65a66fb2ed76dbf5b0'
REFINEMENT_ARCHIVE=dict(case='AP087',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-half-log-exp-refinement-v1/generation-process.json.gz',
    bytes=85657,sha256='7555dcd69f6ae80900d96e595ec07509eac7d3d991bfd2fd47cc8e018028f24a',
    raw_bytes=1569172,raw_sha256='676e04a2a73181d580fe2f86e893a56237a630a6497d717d5cab14dd90a05407',bundle_bytes=927210,
    bundle_sha256='df2878ab2be432ad492885406eec7d5bdff383560a2e4934e947062bdc7b9160',
    nodes=231,root=230,target_ast_sha256='74d9571876bc3c082af4e6ab56b2f18a0e49718f24ef4ea8fe3ddf85f58dcf49')
BUDGET_ARCHIVE=dict(case='AP083',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-log-exp-cutoff-refinement-v1/generation-process.json.gz',
    bytes=89264,sha256='b94b3fa47e7d8c19a723102231f6fd09866a12f57815ff16d8ae2e1aec4c24f4',
    raw_bytes=1680264,raw_sha256='f085dde7c60c761cd5621a635e59abd333fc8af1ee5b9ba8a40e2ea49d44c507',
    bundle_bytes=995536,bundle_sha256='18275d48a04f78840e82c3d6f549a632496ea202cafc32b10de83ef2be0979fa',
    nodes=238,root=237,target_ast_sha256='97d070681313d49334933a292e949acae3f61cc484c18b5a122d05060269d1c5')
ARCHIVES=(REFINEMENT_ARCHIVE,BUDGET_ARCHIVE)
ENDPOINT_SOURCES={'refinement':REFINEMENT_SOURCE,'budgets':BUDGET_SOURCES['budgets'],'arithmetic':BUDGET_SOURCES['arithmetic']}
ENDPOINT_OWNERS=dict(refinement='AP087',budgets='AP083',arithmetic='AP083')
HELPER_DEPENDENCIES={'AP088':tuple(ENDPOINT_SOURCES)}


class HalfLogExpCutoffError(ValueError):
    """Changed half-argument computations, actual powers or proved budget."""


def frozen_half_log_exp_cutoff_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=22 or len(premises)!=15 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise HalfLogExpCutoffError('AP088 exact half-logarithm cutoff target changed')
    return target


def source_contract():
    return dict(code='AP088',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=15,all_actual_logarithm_exponential_and_power_computations_preserved=True,
        original_logarithm_prefix_and_horner_scales_unchanged=True,exponential_arguments_explicitly_halved=True,
        independent_coefficient_scales_codes_and_exp_heads_allowed=True,auxiliary_cutoff='M=18*r+2',
        fine_log_length='M+l',fine_exp_degree='M+1+N',budgets_proved_not_assumed=['54*r<=3^M','4*r<=2^M'],
        finite_error='r*(a0*v)<=r*(b0*u)+a0*b0',monotone_cross_value='b0*u<=a0*v',
        positive_factors_cancelled_only_after_proof=True,doubled_argument_denominators_proved_nonzero=True,
        symbolic_precision_scale=True,zero_r_l_N_and_heads_allowed=True,rational_reading_requires_positive_r_and_heads=True,
        native_constructor_reused_from='AP083',new_arithmetic_helper_needed=False,new_induction_count=0,new_induction_needed=False,
        new_definition_ids=[],definition_admissions=0,analytic_log_exp_identity_claimed=False,analytic_limit_claimed=False,
        sqrt2_identification_claimed=False,fixed_approximation_program_changed=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def half_log_exp_cutoff_source_pins():
    result=half_log_exp_refinement_source_pins()
    for name,pin in log_exp_cutoff_refinement_source_pins().items():
        if name in result and result[name]!=pin:raise HalfLogExpCutoffError('half-log cutoff source disagreement')
        result[name]=pin
    expected={'scripts/sqrt2_power_half_log_exp_refinement.py':'19d862af59e8bc76e8a984390788a447bb870efb11d6776d02bb4f3c7f604929',
        'scripts/sqrt2_power_log_exp_cutoff_refinement.py':'22c1f5539cf98203ad5f4750858c4b1d14aa7ba42009ff6fa6709e5f7b8ae383',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_half_log_exp_cutoff.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise HalfLogExpCutoffError('half-log cutoff source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def prove_half_log_exp_cutoff(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP088',target=frozen_half_log_exp_cutoff_target(_registry=registry),registry=registry,
        helper_sources={},helper_hashes={},endpoint_sources=ENDPOINT_SOURCES,endpoint_owners=ENDPOINT_OWNERS,
        archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories={'AP088':_root},pins=half_log_exp_cutoff_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
