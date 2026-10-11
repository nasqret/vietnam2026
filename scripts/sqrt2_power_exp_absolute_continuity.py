"""AP070: requested absolute finite continuity from an explicit sum majorant.

Keep the two supplied recurrences and independent normalizations. A proved
bound t<=C*b0 and the explicit budget (r*g)*C<=d*e turn AP069's relative
estimate into r*(a0*t)<=r*(b0*s)+a0*b0. The majorant is a premise, not an
analytic fact inserted into a definition; r remains symbolic.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_exp_relative_cross_continuity import (
    ROOT,Scope,introduce,apply,specialize,canonical,json_hash,source_registry,
    exp_relative_cross_continuity_source_pins,NAMED_SOURCE as RELATIVE_SOURCE,
    PARAMETERS as RELATIVE_PARAMETERS,PREMISES as RELATIVE_PREMISES,BOUND_ARCHIVE,
)
from sqrt2_power_quadratic_trace_exists import conjunction
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-absolute-continuity-v1'
PARAMETERS=RELATIVE_PARAMETERS+('C','r')
PREMISES=RELATIVE_PREMISES+('Le(t,C*b0)','Le((r*g)*C,d*e)')
CONCLUSION='Le(b0*s,a0*t) /\\ Le(r*(a0*t),r*(b0*s)+a0*b0)'
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> '+CONCLUSION
TARGET_SHA256='a085e6805bd448394a0ee2f1cd547da010b34b51bebbfe4b683fe338d87aeba9'
HELPER_SOURCES={'arithmetic':'forall p r g C A U V. ~p=0 -> Le(p*V,p*U+g*V) -> Le(V,C*A) -> Le((r*g)*C,p) -> Le(r*V,r*U+A)'}
HELPER_TARGET_SHA256={'arithmetic':'77cd241f1f4df99586251e0d065d132545fa72c914b5041af89f3471fc3b51e3'}
RELATIVE_ARCHIVE=dict(case='AP069',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-relative-cross-continuity-v1/generation-process.json.gz',
    bytes=38471,sha256='5308e44b0cb446c2e8ac48c35425a0af4e36ea25b2ea5e4da799d894cbbad0a4',
    raw_bytes=673583,raw_sha256='10f8a2f005a72b7f3ba609ab9afa9bb5cb1045973ee8eea765686cb6b98b30e7',
    bundle_bytes=384083,bundle_sha256='1f05df465a0a247f69b287823dcc92b3d2c728cb3808e5b3aa561dc6edcec249',
    nodes=144,root=143,target_ast_sha256='bd0a751f36b51993e4a8a1c8d3802afe6e72a7304960b031618cbee1c6e66f62')
ARCHIVES=(RELATIVE_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'relative':RELATIVE_SOURCE,
    'mul_ne_zero':'forall a b. ~a=0 -> ~b=0 -> ~a*b=0',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'mul_right_mono':'forall a b c. Le(a,b) -> Le(a*c,b*c)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)',
    'mul_comm':'forall a b. a*b=b*a','mul_add':'forall a b c. a*(b+c)=a*b+a*c',
    'add_left_mono':'forall a b c. Le(a,b) -> Le(c+a,c+b)',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'mul_le_cancel':'forall c a b. ~c=0 -> Le(c*a,c*b) -> Le(a,b)'}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES};ENDPOINT_OWNERS['relative']='AP069'
HELPER_DEPENDENCIES={'arithmetic':('mul_left_mono','mul_right_mono','mul_assoc','mul_comm','mul_add','add_left_mono','le_trans','mul_le_cancel'),
    'AP070':('relative','mul_ne_zero','mul_left_mono','mul_assoc','mul_comm','arithmetic')}


class ExpAbsoluteContinuityError(ValueError):
    """Changed majorant premise, independent computations or precision budget."""


def definition_registry():
    pool=source_registry();needed=set();pending=['Le','Sum','NatScaledExpRecurrence']
    while pending:
        name=pending.pop()
        if name not in needed:needed.add(name);pending.extend(pool[name].conceptual_dependencies)
    result={name:spec for name,spec in pool.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ExpAbsoluteContinuityError('absolute continuity conservative definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_exp_absolute_continuity_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=16 or len(premises)!=11 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpAbsoluteContinuityError('AP070 exact supplied-majorant absolute continuity changed')
    return target


def source_contract():
    return dict(code='AP070',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=11,both_supplied_recurrences_heads_and_sums_preserved=True,
        independent_denominators_heads_and_codes_allowed=True,argument_gap='d*y=e*x+g',
        actual_sum_majorant_required='t<=C*b0',precision_budget_required='(r*g)*C<=d*e',
        requested_absolute_error='r*(a0*t)<=r*(b0*s)+a0*b0',monotonicity='b0*s<=a0*t',
        symbolic_precision_scale=True,precision_power_constructed=False,majorant_constructed=False,
        zero_arguments_gap_heads_horizon_and_scale_allowed=True,new_induction_needed=False,new_induction_count=0,
        new_definition_ids=[],definition_admissions=0,rational_validity_claimed=False,analytic_continuity_claimed=False,
        fixed_approximation_program_changed=False,original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_absolute_continuity_source_pins():
    result=exp_relative_cross_continuity_source_pins()
    expected={'scripts/sqrt2_power_exp_relative_cross_continuity.py':'2b94325a395b0996433d4d134687fb8f222c9e8d6082ba8479919f170b60e9d5',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_absolute_continuity.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpAbsoluteContinuityError('absolute continuity source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _left(t,registry,proof,right,equality):
    from peano_lab.kernel.terms import pretty_term
    return _subst(t,registry,'Le(slot,'+pretty_term(right,list(t.variables))+')',equality,proof)


def _right(t,registry,proof,left,equality):
    from peano_lab.kernel.terms import pretty_term
    return _subst(t,registry,'Le('+pretty_term(left,list(t.variables))+',slot)',equality,proof)


def _arithmetic(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqSym
    from peano_lab.kernel.terms import Add,Mul
    def finish(t):
        p,r,g,C,A,U,V=t.terms(('p','r','g','C','A','U','V'));rg=Mul(r,g);short=Mul(p,Mul(r,U))
        upper=apply(specialize(t,'mul_left_mono',Mul(p,V),Add(Mul(p,U),Mul(g,V)),r),t.hyp('relative'))
        left=_multiplicative_equal(t,Mul(r,Mul(p,V)),Mul(p,Mul(r,V)))
        right=_chain(specialize(t,'mul_add',r,Mul(p,U),Mul(g,V)),
            CongAdd(_multiplicative_equal(t,Mul(r,Mul(p,U)),short),_multiplicative_equal(t,Mul(r,Mul(g,V)),Mul(rg,V))))
        upper=_left(t,registry,upper,Mul(r,Add(Mul(p,U),Mul(g,V))),left)
        upper=_right(t,registry,upper,Mul(p,Mul(r,V)),right)
        error=apply(specialize(t,'mul_left_mono',V,Mul(C,A),rg),t.hyp('majorant'))
        error=_right(t,registry,error,Mul(rg,V),EqSym(specialize(t,'mul_assoc',rg,C,A)))
        budget=apply(specialize(t,'mul_right_mono',Mul(rg,C),p,A),t.hyp('budget'))
        error=apply(specialize(t,'le_trans',Mul(rg,V),Mul(Mul(rg,C),A),Mul(p,A)),error,budget)
        error=apply(specialize(t,'add_left_mono',Mul(rg,V),Mul(p,A),short),error)
        upper=apply(specialize(t,'le_trans',Mul(p,Mul(r,V)),Add(short,Mul(rg,V)),Add(short,Mul(p,A))),upper,error)
        upper=_right(t,registry,upper,Mul(p,Mul(r,V)),EqSym(specialize(t,'mul_add',p,Mul(r,U),A)))
        return apply(specialize(t,'mul_le_cancel',p,Mul(r,V),Add(Mul(r,U),A)),t.hyp('nonzero'),upper)
    return introduce(s,('p','r','g','C','A','U','V'),('nonzero','relative','majorant','budget'),finish)


def _root(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Mul
    def finish(t):
        d,e,g,a,b,u,v,C,r=t.terms(('d','e','g','a0','b0','s','t','C','r'))
        relative=apply(specialize(t,'relative',*t.terms(RELATIVE_PARAMETERS)),*(t.hyp(name) for name in
            ('nonzero_d','nonzero_e','gap','recurrence_a','recurrence_b','head_a','head_b','sum_a','sum_b')))
        positive=apply(specialize(t,'mul_ne_zero',d,e),t.hyp('nonzero_d'),t.hyp('nonzero_e'))
        bound=apply(specialize(t,'mul_left_mono',v,Mul(C,b),a),t.hyp('majorant'))
        bound=_right(t,registry,bound,Mul(a,v),_multiplicative_equal(t,Mul(a,Mul(C,b)),Mul(C,Mul(a,b))))
        error=apply(specialize(t,'arithmetic',Mul(d,e),r,g,C,Mul(a,b),Mul(b,u),Mul(a,v)),positive,AndElimR(relative),bound,t.hyp('budget'))
        return conjunction(AndElimL(relative),error)
    return introduce(s,PARAMETERS,('nonzero_d','nonzero_e','gap','recurrence_a','recurrence_b','head_a','head_b','sum_a','sum_b','majorant','budget'),finish)


def prove_exp_absolute_continuity(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP070',target=frozen_exp_absolute_continuity_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'arithmetic':lambda s:_arithmetic(s,registry),'AP070':lambda s:_root(s,registry)},
        pins=exp_absolute_continuity_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
