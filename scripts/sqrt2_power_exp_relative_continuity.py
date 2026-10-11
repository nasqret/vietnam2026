"""AP068: finite relative continuity without an argument-size restriction.

For equal heads and y=x+g, the actual sums satisfy s<=t and
d*t<=d*s+g*t. Reuse the unrestricted term-difference and actual tail-slice
proofs, bounding the preceding prefix by t rather than by a small-argument
constant. An absolute majorant remains a separate obligation.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_exp_sum_continuity import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,canonical,json_hash,
    definition_registry as source_registry,exp_sum_continuity_source_pins,
    HELPER_SOURCES as CONTINUITY_HELPERS,PARAMETERS,FIXED,A,B,TA,TB,COMMON,
    SUM_BOUND_SOURCE,SUM_BOUND_ARCHIVE,BOUND_ARCHIVE,
)
from sqrt2_power_exp_cross_continuity import CONTINUITY_ARCHIVE
from sqrt2_power_series_power_trace import CONVOLUTION_ARCHIVE
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-relative-continuity-v1'
PREMISES=COMMON+('Sum(ab,ac,S N,s)','Sum(bb,bc,S N,t)')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> Le(s,t) /\\ Le(d*t,d*s+g*t)'
TARGET_SHA256='44c446356566e235233dd3597393197285525996f1312f828627e5f6c621ea1d'
HELPER_SOURCES={'arithmetic':'forall d g a0 s t u v w. s=a0+u -> t=a0+v -> Le(u,v) -> Le(d*v,d*u+g*w) -> Le(w,t) -> Le(s,t) /\\ Le(d*t,d*s+g*t)'}
HELPER_TARGET_SHA256={'arithmetic':'a53028e3403944731f72facdc0c22d559b028d2ecdab5b25d6b79bc1c0597cb6'}
ARCHIVES=(CONTINUITY_ARCHIVE,SUM_BOUND_ARCHIVE,CONVOLUTION_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={name:CONTINUITY_HELPERS[name] for name in ('split_head','prefix_below','tail_graphs')}
ENDPOINT_SOURCES.update(sum_bound=SUM_BOUND_SOURCE,
    sum_exists='forall b c N. exists n. Sum(b,c,N,n)',
    add_left_mono='forall a b c. Le(a,b) -> Le(c+a,c+b)',
    mul_left_mono='forall a b c. Le(a,b) -> Le(c*a,c*b)',
    le_trans='forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    mul_add='forall a b c. a*(b+c)=a*b+a*c',
    add_assoc='forall a b c. (a+b)+c=a+(b+c)',
    one_mul='forall a. 1*a=a',zero_mul='forall a. 0*a=0')
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(split_head='CV096',prefix_below='CV096',tail_graphs='CV096',sum_bound='CV095',sum_exists='CV003')
HELPER_DEPENDENCIES={'arithmetic':('add_left_mono','mul_left_mono','le_trans','mul_add','add_assoc'),
    'AP068':('split_head','tail_graphs','sum_bound','sum_exists','prefix_below','arithmetic','one_mul','zero_mul')}


class ExpRelativeContinuityError(ValueError):
    """Changed actual sums, common head or relative error coefficient."""


def definition_registry():
    pool=source_registry();needed=set();pending=['Le','Sum','NatAffineSlice','NatLinearBound','NatScaledExpRecurrence']
    while pending:
        name=pending.pop()
        if name not in needed:needed.add(name);pending.extend(pool[name].conceptual_dependencies)
    result={name:spec for name,spec in pool.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ExpRelativeContinuityError('relative continuity conservative definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_exp_relative_continuity_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=12 or len(premises)!=8 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpRelativeContinuityError('AP068 exact unrestricted relative finite continuity changed')
    return target


def source_contract():
    return dict(code='AP068',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=8,both_supplied_recurrences_heads_and_sums_preserved=True,
        common_argument_denominator_and_head_required=True,argument_gap='y=x+g',
        argument_upper_bound_required=False,monotonicity='s<=t',relative_error='d*t<=d*s+g*t',
        actual_tail_slices_and_preceding_prefix_constructed=True,
        zero_arguments_gap_heads_and_horizon_allowed=True,new_induction_needed=False,new_induction_count=0,
        new_definition_ids=[],definition_admissions=0,absolute_majorant_claimed=False,
        analytic_continuity_claimed=False,fixed_approximation_program_changed=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_relative_continuity_source_pins():
    result=exp_sum_continuity_source_pins()
    expected={'scripts/sqrt2_power_exp_sum_continuity.py':'92e7667198420bf1e508d1aafd59e29c7875a163dea8ab3e012e224b1c614f9e',
        'scripts/sqrt2_power_exp_cross_continuity.py':'df8ebc21517107b814a6f1e55903bb412d37a5b09917eeef6a47930b557b0bcd',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_relative_continuity.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpRelativeContinuityError('relative continuity source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul
    def finish(t):
        d,g,a0,out,full,u,v,w=t.terms(('d','g','a0','s','t','u','v','w'))
        lower=apply(specialize(t,'add_left_mono',u,v,a0),t.hyp('tail_monotone'))
        lower=_subst(t,registry,'Le(slot,a0+v)',EqSym(t.hyp('split_a')),lower)
        lower=_subst(t,registry,'Le(s,slot)',EqSym(t.hyp('split_b')),lower)
        da0,du,dv,gw=Mul(d,a0),Mul(d,u),Mul(d,v),Mul(g,w)
        upper=apply(specialize(t,'add_left_mono',dv,Add(du,gw),da0),t.hyp('tail_difference'))
        left=_chain(CongMul(EqRefl(d),t.hyp('split_b')),specialize(t,'mul_add',d,a0,v))
        upper=_subst(t,registry,'Le(slot,d*a0+(d*u+g*w))',EqSym(left),upper)
        right=_chain(EqSym(specialize(t,'add_assoc',da0,du,gw)),
            CongAdd(EqSym(specialize(t,'mul_add',d,a0,u)),EqRefl(gw)),
            CongAdd(CongMul(EqRefl(d),EqSym(t.hyp('split_a'))),EqRefl(gw)))
        upper=_subst(t,registry,'Le(d*t,slot)',right,upper)
        remainder=apply(specialize(t,'mul_left_mono',w,full,g),t.hyp('prefix_below'))
        remainder=apply(specialize(t,'add_left_mono',gw,Mul(g,full),Mul(d,out)),remainder)
        return conjunction(lower,apply(specialize(t,'le_trans',Mul(d,full),Add(Mul(d,out),gw),Add(Mul(d,out),Mul(g,full))),upper,remainder))
    return introduce(s,('d','g','a0','s','t','u','v','w'),('split_a','split_b','tail_monotone','tail_difference','prefix_below'),finish)


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqRefl
    from peano_lab.kernel.terms import Succ,Zero
    one=Succ(Zero())
    def chosen(t):
        d,g,N,a0,out,full,u,v,w=t.terms(('d','g','N','a0','s','t','u','v','w'))
        tail_a,tail_b=t.hyp('tail_a'),t.hyp('tail_b')
        graphs=apply(specialize(t,'tail_graphs',*t.terms(FIXED+TA+TB)),*(t.hyp(label) for label in
            ('nonzero','gap','recurrence_a','recurrence_b','head_a','head_b')),field(tail_a,0,3),field(tail_b,0,3))
        lower=apply(specialize(t,'sum_bound',one,Zero(),one,*t.terms(TB+B+TA),N,v,w,u),
            field(graphs,1,2),field(tail_b,1,3),t.hyp('prefix_sum'),field(tail_a,1,3))
        lower=_subst(t,registry,'Le(slot,1*v+0*w)',specialize(t,'one_mul',u),lower)
        simplify=_chain(CongAdd(specialize(t,'one_mul',v),specialize(t,'zero_mul',w)),instantiate(Axiom('PA3'),v))
        lower=_subst(t,registry,'Le(u,slot)',simplify,lower)
        upper=apply(specialize(t,'sum_bound',d,g,d,*t.terms(TA+B+TB),N,u,w,v),
            field(graphs,0,2),field(tail_a,1,3),t.hyp('prefix_sum'),field(tail_b,1,3))
        below=apply(specialize(t,'prefix_below',*t.terms(B),N,w,full),t.hyp('prefix_sum'),t.hyp('sum_b'))
        return apply(specialize(t,'arithmetic',d,g,a0,out,full,u,v,w),field(tail_a,2,3),field(tail_b,2,3),lower,upper,below)
    return introduce(s,PARAMETERS,('nonzero','gap','recurrence_a','recurrence_b','head_a','head_b','sum_a','sum_b'),lambda t:
        eliminate(t,apply(specialize(t,'split_head',*t.terms(A+('N','a0','s'))),t.hyp('head_a'),t.hyp('sum_a')),TA+('u',),'tail_a',lambda u:
            eliminate(u,apply(specialize(u,'split_head',*u.terms(B+('N','a0','t'))),u.hyp('head_b'),u.hyp('sum_b')),TB+('v',),'tail_b',lambda v:
                eliminate(v,specialize(v,'sum_exists',*v.terms(B+('N',))),('w',),'prefix_sum',chosen))))


def prove_exp_relative_continuity(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP068',target=frozen_exp_relative_continuity_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'arithmetic':lambda s:_arithmetic(s,registry),'AP068':lambda s:_root(s,registry)},
        pins=exp_relative_continuity_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
