"""AP069: unrestricted relative continuity across independent rational codes.

Actual rescaling constructs common-denominator, common-head tables. Apply
AP068 to their actual sums and transport the resulting inequalities back.
The error remains relative, and initial heads need not be positive.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_exp_relative_continuity import (
    ROOT,Scope,introduce,eliminate,field,apply,specialize,canonical,json_hash,
    source_registry,exp_relative_continuity_source_pins,NAMED_SOURCE as CONTINUITY_SOURCE,BOUND_ARCHIVE,
)
from sqrt2_power_exp_cross_continuity import A,B,U,V,PARAMETERS,RESCALING_ARCHIVE
from sqrt2_power_exp_rescaling import NAMED_SOURCE as RESCALING_SOURCE,exp_rescaling_source_pins
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-relative-cross-continuity-v1'
PREMISES=('~d=0','~e=0','d*y=e*x+g',
    'NatScaledExpRecurrence(d,x,ab,ac,N)','NatScaledExpRecurrence(e,y,bb,bc,N)',
    'BetaAt(ab,ac,0,a0)','BetaAt(bb,bc,0,b0)','Sum(ab,ac,S N,s)','Sum(bb,bc,S N,t)')
CONCLUSION='Le(b0*s,a0*t) /\\ Le((d*e)*(a0*t),(d*e)*(b0*s)+g*(a0*t))'
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> '+CONCLUSION
TARGET_SHA256='bd0a751f36b51993e4a8a1c8d3802afe6e72a7304960b031618cbee1c6e66f62'
RELATIVE_ARCHIVE=dict(case='AP068',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-relative-continuity-v1/generation-process.json.gz',
    bytes=36067,sha256='25e2b3cfe350816851c2e7068f0f2226827e5412e12d9e6e1b841a06b7da4dfb',
    raw_bytes=590454,raw_sha256='9f12ff1bf1237b5007ec581de657052bb141d3cf10d121d2718dfb70b36ea39d',
    bundle_bytes=331452,bundle_sha256='0fa098dd5ca136b1341a37b5c0e3ef5211e1d8316588a5601d47c9d8d43f68df',
    nodes=137,root=136,target_ast_sha256='44c446356566e235233dd3597393197285525996f1312f828627e5f6c621ea1d')
ARCHIVES=(RELATIVE_ARCHIVE,RESCALING_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'continuity':CONTINUITY_SOURCE,'rescaling':RESCALING_SOURCE,
    'mul_ne_zero':'forall a b. ~a=0 -> ~b=0 -> ~a*b=0',
    'mul_comm':'forall a b. a*b=b*a'}
ENDPOINT_OWNERS=dict(continuity='AP068',rescaling='CV097',mul_ne_zero='CV071',mul_comm='CV071')
HELPER_DEPENDENCIES={'AP069':tuple(ENDPOINT_SOURCES)}


class ExpRelativeCrossContinuityError(ValueError):
    """Changed independent inputs, exact rational gap or relative error."""


def definition_registry():
    pool=source_registry();needed=set();pending=['Le','Sum','NatLinearTriple','NatScaledExpRecurrence']
    while pending:
        name=pending.pop()
        if name not in needed:needed.add(name);pending.extend(pool[name].conceptual_dependencies)
    result={name:spec for name,spec in pool.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ExpRelativeCrossContinuityError('relative cross-continuity conservative definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_exp_relative_cross_continuity_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=14 or len(premises)!=9 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpRelativeCrossContinuityError('AP069 exact independent relative finite continuity changed')
    return target


def source_contract():
    return dict(code='AP069',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=9,both_supplied_recurrences_heads_and_sums_preserved=True,
        independent_argument_denominators_heads_and_codes_allowed=True,
        actual_common_denominator_and_head_tables_constructed=True,argument_gap='d*y=e*x+g',
        argument_upper_bound_required=False,monotonicity='b0*s<=a0*t',
        relative_error='(d*e)*(a0*t)<=(d*e)*(b0*s)+g*(a0*t)',
        zero_arguments_gap_heads_and_horizon_allowed=True,new_induction_needed=False,new_induction_count=0,
        new_definition_ids=[],definition_admissions=0,absolute_majorant_claimed=False,
        code_number_equality_claimed=False,rational_validity_claimed=False,analytic_continuity_claimed=False,
        fixed_approximation_program_changed=False,original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_relative_cross_continuity_source_pins():
    result=exp_relative_continuity_source_pins()
    for name,pin in exp_rescaling_source_pins().items():
        if name in result and result[name]!=pin:
            raise ExpRelativeCrossContinuityError('relative cross-continuity source disagreement')
        result[name]=pin
    expected={'scripts/sqrt2_power_exp_relative_continuity.py':'dbbd9f2e5831f64f1cea19d6d7ba54b246e9f171e245acf47d5aee87ca70ff9f',
        'scripts/sqrt2_power_exp_rescaling.py':'bc2721198e4ce3580b7965152fe3b6e02b41336dde024eb543e64069844d6947',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_relative_cross_continuity.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpRelativeCrossContinuityError('relative cross-continuity source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _root(s,registry):
    from peano_lab.kernel.terms import Mul
    def finish(t):
        a,b=t.hyp('scaled_a'),t.hyp('scaled_b')
        d,e,x,y,g,N,a0,b0,u,v=t.terms(('d','e','x','y','g','N','a0','b0','u','v'))
        nonzero=apply(specialize(t,'mul_ne_zero',d,e),t.hyp('nonzero_d'),t.hyp('nonzero_e'))
        recurrence=_subst(t,registry,'NatScaledExpRecurrence(slot,d*y,vb,vc,N)',specialize(t,'mul_comm',e,d),field(b,1,5))
        head=_subst(t,registry,'BetaAt(ub,uc,0,slot)',specialize(t,'mul_comm',b0,a0),field(a,2,5))
        result=apply(specialize(t,'continuity',Mul(d,e),Mul(e,x),Mul(d,y),g,N,*t.terms(U+V),Mul(a0,b0),u,v),
            nonzero,t.hyp('gap'),field(a,1,5),recurrence,head,field(b,2,5),field(a,3,5),field(b,3,5))
        result=_subst(t,registry,'Le(slot,v) /\\ Le((d*e)*v,(d*e)*slot+g*v)',field(a,4,5),result)
        return _subst(t,registry,'Le(b0*s,slot) /\\ Le((d*e)*slot,(d*e)*(b0*s)+g*slot)',field(b,4,5),result)
    def second(t):
        scaled=apply(specialize(t,'rescaling',*t.terms(('e','y','d','a0','N')+B+('b0','t'))),
            t.hyp('recurrence_b'),t.hyp('head_b'),t.hyp('sum_b'))
        return eliminate(t,scaled,V+('v',),'scaled_b',finish)
    def first(t):
        scaled=apply(specialize(t,'rescaling',*t.terms(('d','x','e','b0','N')+A+('a0','s'))),
            t.hyp('recurrence_a'),t.hyp('head_a'),t.hyp('sum_a'))
        return eliminate(t,scaled,U+('u',),'scaled_a',second)
    return introduce(s,PARAMETERS,('nonzero_d','nonzero_e','gap','recurrence_a','recurrence_b','head_a','head_b','sum_a','sum_b'),first)


def prove_exp_relative_cross_continuity(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP069',target=frozen_exp_relative_cross_continuity_target(_registry=registry),registry=registry,
        helper_sources={},helper_hashes={},endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'AP069':lambda s:_root(s,registry)},pins=exp_relative_cross_continuity_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
