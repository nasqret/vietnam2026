"""AP035: every actual finite exponential recurrence has factorial terms.

Induct on the term index, retaining the caller's table and head. The identity
(T[j]*j!)*d^j = h*x^j follows by multiplication, never cancellation. Hence
zero d, zero x, zero head and the empty recurrence horizon are all allowed.
Rational validity and infinite-series interpretation remain separate.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_scaled_exp_terms import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry as source_registry,
)
from sqrt2_power_scaled_exp_bound import EXP_ARCHIVE
from sqrt2_power_weight_factorials import ENDPOINT_SOURCES as FACTORIAL_ENDPOINTS,HELPER_SOURCES as WEIGHT_HELPERS
from sqrt2_power_log_exp_witness import log_exp_witness_source_pins
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-recurrence-normalization-v1'
FIXED=('d','x','tb','tc','N','h')
INVARIANT='forall j t f p q. Le(j,N) -> BetaAt(tb,tc,j,t) -> Factorial(j,f) -> Pow(d,j,p) -> Pow(x,j,q) -> (t*f)*p=h*q'
NAMED_SOURCE='forall '+' '.join(FIXED)+'. NatScaledExpRecurrence(d,x,tb,tc,N) -> BetaAt(tb,tc,0,h) -> '+INVARIANT
TARGET_SHA256='9b47638db02d23a2bbc549793da14c71bc39b811db179fadbf3410e4723bbdf6'
HELPER_SOURCES,HELPER_TARGET_SHA256={},{}
ARCHIVES=(EXP_ARCHIVE,)
ENDPOINT_SOURCES={name:FACTORIAL_ENDPOINTS[name] for name in ('factorial_zero','factorial_step','power_zero','power_step')}
ENDPOINT_SOURCES.update(
    beta_exists='forall b c i. exists a. BetaAt(b,c,i,a)',
    beta_unique='forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d',
    le_refl='forall a. Le(a,a)',le_succ='forall a b. Le(a,b) -> Le(a,S b)',
    le_trans='forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    mul_one='forall a. a*1=a',mul_assoc='forall a b c. (a*b)*c=a*(b*c)',mul_comm='forall a b. a*b=b*a',
    shuffle=WEIGHT_HELPERS['shuffle'])
ENDPOINT_OWNERS={name:'CV070' for name in ENDPOINT_SOURCES}
HELPER_DEPENDENCIES={'AP035':tuple(ENDPOINT_SOURCES)}


class ExpRecurrenceNormalizationError(ValueError):
    """Changed supplied table, head, bounded recurrence or normalization."""


def definition_registry():
    pool=source_registry();needed=set();pending=['Le','BetaAt','Pow','Factorial','NatScaledExpRecurrence']
    while pending:
        name=pending.pop()
        if name not in needed:
            needed.add(name);pending.extend(pool[name].conceptual_dependencies)
    result={name:spec for name,spec in pool.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ExpRecurrenceNormalizationError('existing recurrence definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_exp_recurrence_normalization_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Forall
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=6 or len(premises)!=2 or type(conclusion) is not Forall or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpRecurrenceNormalizationError('AP035 exact supplied recurrence normalization changed')
    return target


def source_contract():
    return dict(code='AP035',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=2,actual_supplied_table_and_head_preserved=True,
        all_in_range_entries_and_actual_factorials_powers=True,
        zero_input_denominator_numerator_head_and_horizon_allowed=True,
        exact_integer_normalization='(T[j]*j!)*d^j=h*x^j',cancellation_used=False,
        new_induction_needed=True,new_induction_count=1,new_definition_ids=[],definition_admissions=0,
        rational_validity_claim=False,analytic_exponential_identity=False,analytic_limit_claim=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_recurrence_normalization_source_pins():
    result=log_exp_witness_source_pins()
    expected={'scripts/sqrt2_power_log_exp_witness.py':'19b9cc3b4f66db42decc879fca3df056136e02c80c86e6b5fd1369c47d5df16f',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_recurrence_normalization.py'):
        with (ROOT/name).open('rb') as stream: raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpRecurrenceNormalizationError('recurrence normalization source or archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _root(s,target):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Mul,Succ,Zero
    row_params=('t','f','p','q');row_hyps=('bound','entry','factorial','den_power','num_power')
    def base(t):
        value,f,p,q,h=t.terms(('t','f','p','q','h'));zero=Zero()
        value_eq=apply(specialize(t,'beta_unique',*t.terms(('tb','tc')),zero,value,h),t.hyp('entry'),t.hyp('head'))
        f_eq=apply(specialize(t,'factorial_zero',zero,f),EqRefl(zero),t.hyp('factorial'))
        p_eq=apply(specialize(t,'power_zero',t.term('d'),zero,p),EqRefl(zero),t.hyp('den_power'))
        q_eq=apply(specialize(t,'power_zero',t.term('x'),zero,q),EqRefl(zero),t.hyp('num_power'))
        one=Succ(zero)
        left=_chain(CongMul(CongMul(value_eq,f_eq),p_eq),
            CongMul(specialize(t,'mul_one',h),EqRefl(one)),specialize(t,'mul_one',h))
        right=_chain(CongMul(EqRefl(h),q_eq),specialize(t,'mul_one',h))
        return _chain(left,EqSym(right))
    def successor(t):
        def chosen(u):
            j,N,d,x,value,h,old,f0,p0,q0=u.terms(('j','N','d','x','t','h','old_t','old_f','old_p','old_q'));sj=Succ(j)
            bound=apply(specialize(u,'le_trans',j,sj,N),
                apply(specialize(u,'le_succ',j,j),specialize(u,'le_refl',j)),u.hyp('bound'))
            old_identity=apply(specialize(u,'IH',old,f0,p0,q0),bound,u.hyp('old_entry'),
                AndElimL(u.hyp('factorial_data')),AndElimL(u.hyp('den_data')),AndElimL(u.hyp('num_data')))
            adjacent=apply(specialize(u,'recurrence',j,old,value),u.hyp('bound'),u.hyp('old_entry'),u.hyp('entry'))
            return _chain(CongMul(CongMul(EqRefl(value),AndElimR(u.hyp('factorial_data'))),AndElimR(u.hyp('den_data'))),
                specialize(u,'shuffle',value,f0,p0,sj,d),CongMul(CongMul(adjacent,EqRefl(f0)),EqRefl(p0)),
                _multiplicative_equal(u,Mul(Mul(Mul(x,old),f0),p0),Mul(x,Mul(Mul(old,f0),p0))),
                CongMul(EqRefl(x),old_identity),_multiplicative_equal(u,Mul(x,Mul(h,q0)),Mul(h,Mul(q0,x))),
                CongMul(EqRefl(h),EqSym(AndElimR(u.hyp('num_data')))))
        j=t.term('j');sj=Succ(j)
        fact=apply(specialize(t,'factorial_step',j,sj,t.term('f')),EqRefl(sj),t.hyp('factorial'))
        return eliminate(t,fact,('old_f',),'factorial_data',lambda u:
            eliminate(u,apply(specialize(u,'power_step',u.term('d'),u.term('j'),Succ(u.term('j')),u.term('p')),
                EqRefl(Succ(u.term('j'))),u.hyp('den_power')),('old_p',),'den_data',lambda v:
                eliminate(v,apply(specialize(v,'power_step',v.term('x'),v.term('j'),Succ(v.term('j')),v.term('q')),
                    EqRefl(Succ(v.term('j'))),v.hyp('num_power')),('old_q',),'num_data',lambda w:
                    eliminate(w,specialize(w,'beta_exists',*w.terms(('tb','tc','j'))),('old_t',),'old_entry',chosen))))
    motive=target
    for _ in FIXED: motive=motive.body
    motive=motive.right.right.body
    return introduce(s,FIXED,('recurrence','head'),lambda t:Ind(motive,
        introduce(t,row_params,row_hyps,base),introduce(t,('j',),('IH',),lambda u:introduce(u,row_params,row_hyps,successor))))


def prove_exp_recurrence_normalization(*,limits=None):
    registry=definition_registry();target=frozen_exp_recurrence_normalization_target(_registry=registry)
    return assemble_mixed_certificate(code='AP035',target=target,registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'AP035':lambda s:_root(s,target)},pins=exp_recurrence_normalization_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=1)
