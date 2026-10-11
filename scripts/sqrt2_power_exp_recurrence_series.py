"""AP036: actual recurrence terms are valid rational factorial-series terms.

Use AP035's normalization and AP021's generic term construction, retaining
the caller's exact table and head. Positivity is required only for rational
denominators. Zero numerator, zero index and zero horizon remain allowed.
No analytic limit or infinite-series identity is asserted.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_exp_recurrence_normalization import (
    ROOT,Scope,introduce,apply,specialize,canonical,json_hash,
    NAMED_SOURCE as NORMALIZATION_SOURCE,exp_recurrence_normalization_source_pins,
)
from sqrt2_power_finite_exp_series import (
    HELPER_SOURCES as SERIES_HELPERS,definition_registry as source_registry,
    finite_exp_series_source_pins,term_formula,
)
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-recurrence-series-v1'
PARAMETERS=('d','x','tb','tc','N','h')
TERMS=term_formula('x','d','N').replace('w0','h')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. ~d=0 -> ~h=0 -> NatScaledExpRecurrence(d,x,tb,tc,N) -> BetaAt(tb,tc,0,h) -> '+TERMS
TARGET_SHA256='88e50501342eaa8afeb980d49d5c37f6d456c6f32acfa9cabd11f610e93e959c'
HELPER_SOURCES,HELPER_TARGET_SHA256={},{}
NORMALIZATION_ARCHIVE=dict(case='AP035',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-recurrence-normalization-v1/generation-process.json.gz',
    bytes=33222,sha256='7442c7a1680e0f3db7022cfbec8287a22c40e48f824117578888c348755cf297',
    raw_bytes=257515,raw_sha256='e12a51b6a6b812e14910642cc71f9544335c332ac788e2872f2e834c451b22bf',
    bundle_bytes=108842,bundle_sha256='9cca6b66aa1a938f46ea6ec4dc47503a586239318bc48d616d5d68f48b8ee4bc',
    nodes=36,root=35,target_ast_sha256='9b47638db02d23a2bbc549793da14c71bc39b811db179fadbf3410e4723bbdf6')
SERIES_ARCHIVE=dict(case='AP021',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-finite-exp-series-v1/generation-process.json.gz',
    bytes=55410,sha256='a2617b7420004548c65a38e491f2dd6cf4c8bb92cdf07107311d3df2fab0b763',
    raw_bytes=770680,raw_sha256='be13437a0f7abcf5b1e7fce840cf83b2f35a80ffce0498851a8d2f2aa6fd802f',
    bundle_bytes=427389,bundle_sha256='54f2e7c6dafc48993d063b9a2d83baf25bd914591746ff2119806debafd152dd',
    nodes=160,root=159,target_ast_sha256='8c30669eb1c317280a38fcade33d35967d3427cb940f0753752a02da1460daee')
ARCHIVES=(NORMALIZATION_ARCHIVE,SERIES_ARCHIVE)
ENDPOINT_SOURCES=dict(normalization=NORMALIZATION_SOURCE,terms=SERIES_HELPERS['terms'])
ENDPOINT_OWNERS=dict(normalization='AP035',terms='AP021')
HELPER_DEPENDENCIES={'AP036':('normalization','terms')}


class ExpRecurrenceSeriesError(ValueError):
    """Changed rational term, denominator, actual recurrence or ancestor."""


def definition_registry():
    pool=source_registry();needed=set();pending=['Le','BetaAt','Pow','Factorial','NatScaledExpRecurrence','IRatEq']
    while pending:
        name=pending.pop()
        if name not in needed:
            needed.add(name);pending.extend(pool[name].conceptual_dependencies)
    result={name:spec for name,spec in pool.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ExpRecurrenceSeriesError('existing recurrence/rational definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_exp_recurrence_series_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Forall
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=6 or len(premises)!=4 or type(conclusion) is not Forall or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpRecurrenceSeriesError('AP036 exact valid rational factorial terms changed')
    return target


def source_contract():
    return dict(code='AP036',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,actual_supplied_table_and_head_preserved=True,
        positive_input_denominator_and_head_required=True,
        all_in_range_factorials_and_both_powers_constructed=True,
        term_denominators_proved_nonzero=True,zero_numerator_index_and_horizon_allowed=True,
        finite_term_value='T[j]/h=x^j/(j!*d^j)',actual_generic_AP021_term_body_replayed=True,
        unrelated_AP021_sample_root_replayed=False,new_induction_needed=False,new_induction_count=0,
        new_definition_ids=[],definition_admissions=0,analytic_exponential_identity=False,
        analytic_limit_claim=False,original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_recurrence_series_source_pins():
    result=exp_recurrence_normalization_source_pins()
    for name,pin in finite_exp_series_source_pins().items():
        if name in result and result[name]!=pin:
            raise ExpRecurrenceSeriesError('recurrence-series source disagreement')
        result[name]=pin
    expected={'scripts/sqrt2_power_exp_recurrence_normalization.py':'8e9cc376cfd192274f4f28efcab5f138fedc3a968a5a741e9ef55341ef65a82f',
        'scripts/sqrt2_power_finite_exp_series.py':'ce6d531a982e367ee2df35dcccfbbe7270115f31fcce5097ad3ea1b48c0534ea',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_recurrence_series.py'):
        with (ROOT/name).open('rb') as stream: raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpRecurrenceSeriesError('recurrence-series source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _root(s):
    def finish(t):
        normalized=apply(specialize(t,'normalization',*t.terms(PARAMETERS)),t.hyp('recurrence'),t.hyp('head'))
        return apply(specialize(t,'terms',*t.terms(('x','d','h','tb','tc','N'))),
            t.hyp('head_nonzero'),t.hyp('denominator_nonzero'),normalized)
    return introduce(s,PARAMETERS,('denominator_nonzero','head_nonzero','recurrence','head'),finish)


def prove_exp_recurrence_series(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP036',target=frozen_exp_recurrence_series_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'AP036':_root},pins=exp_recurrence_series_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
