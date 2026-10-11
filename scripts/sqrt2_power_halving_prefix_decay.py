"""AP053: a supplied finite halving prefix has explicit binary decay.

One ordinary HA induction on the index proves 2^k*a[k]<=a[0]. The power
and decoded entries are actual supplied computations, including index zero
and a zero head. There is no division or infinite-sequence assumption.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_exp_large_argument_ratio import (
    ROOT,Scope,introduce,apply,specialize,canonical,json_hash,
    exp_large_argument_ratio_source_pins,BOUND_ARCHIVE,
)
from sqrt2_power_scaled_exp_tail import eliminate,definition_registry as source_registry
from sqrt2_power_half_log_precision import COMPARISON_ARCHIVE
from sqrt2_power_exp_two_sided_continuity import _left,_right
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-halving-prefix-decay-v1'
A=('ab','ac')
PARAMETERS=('k',)+A+('N','a0','a','p')
PREMISES=('Le(k,N)','NatRatioBoundPrefix(ab,ac,1,S N)',
    'BetaAt(ab,ac,0,a0)','BetaAt(ab,ac,k,a)','Pow(2,k,p)')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> Le(p*a,a0)'
TARGET_SHA256='07ae73101d211aba3dfdb13a23c81410079b1c0ab2cde23e58d19ff2b5e0d6d8'
ARCHIVES=(COMPARISON_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={
    'power_zero':'forall d n p. n=0 -> Pow(d,n,p) -> p=1',
    'power_step':'forall d n sn p. sn=S n -> Pow(d,sn,p) -> exists q. Pow(d,n,q) /\\ p=q*d',
    'beta_exists':'forall b c i. exists a. BetaAt(b,c,i,a)',
    'beta_unique':'forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d',
    'le_refl':'forall a. Le(a,a)','le_succ':'forall a b. Le(a,b) -> Le(a,S b)',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'succ_le_succ':'forall a b. Le(a,b) -> Le(S a,S b)',
    'one_mul':'forall a. 1*a=a',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)',
}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(power_zero='AP010',power_step='AP010')
HELPER_DEPENDENCIES={'AP053':tuple(ENDPOINT_SOURCES)}


class HalvingPrefixDecayError(ValueError):
    """Changed actual prefix, power, head, index or exact error bound."""


def definition_registry():
    pool=source_registry();needed=set();pending=['Le','NatRatioBoundPrefix','Pow']
    while pending:
        name=pending.pop()
        if name not in needed:needed.add(name);pending.extend(pool[name].conceptual_dependencies)
    result={name:spec for name,spec in pool.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise HalvingPrefixDecayError('existing halving-prefix definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_halving_prefix_decay_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=7 or len(premises)!=5 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise HalvingPrefixDecayError('AP053 exact supplied halving-prefix decay changed')
    return target


def source_contract():
    return dict(code='AP053',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=5,supplied_power_and_decoded_entries_required=True,finite_prefix_length='N+1',
        index_range='k<=N',halving_parameter=1,dyadic_decay='p*a<=a0, with p=2^k',
        zero_index_horizon_and_head_allowed=True,new_induction_needed=True,new_induction_count=1,
        new_definition_ids=[],definition_admissions=0,large_ground_power_materialized=False,
        infinite_tail_or_exponential_claimed=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def halving_prefix_decay_source_pins():
    result=exp_large_argument_ratio_source_pins()
    expected={'scripts/sqrt2_power_exp_large_argument_ratio.py':'802c21d935e839727000fa781d27c44f40973fd7324b108aabb9842db0b6947e',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_halving_prefix_decay.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise HalvingPrefixDecayError('halving-prefix source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _decay(s,target,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Mul,Succ,Zero
    zero=Zero();two=Succ(Succ(zero))
    row_parameters=A+('N','a0','a','p');row_hyps=('bound','ratio','head','value','power')
    def base(t):
        a,a0,p=t.terms(('a','a0','p'))
        p1=apply(specialize(t,'power_zero',two,zero,p),EqRefl(zero),t.hyp('power'))
        entry=apply(specialize(t,'beta_unique',*t.terms(A),zero,a,a0),t.hyp('value'),t.hyp('head'))
        same=_chain(CongMul(p1,EqRefl(a)),specialize(t,'one_mul',a),entry)
        return _left(t,registry,specialize(t,'le_refl',a0),a0,EqSym(same))
    def chosen(t):
        k,N,a0,a,p,q,b=t.terms(('k','N','a0','a','p','q','b'));sk=Succ(k)
        earlier=apply(specialize(t,'le_trans',k,sk,N),
            apply(specialize(t,'le_succ',k,k),specialize(t,'le_refl',k)),t.hyp('bound'))
        old=apply(specialize(t,'IH',*t.terms(A),N,a0,b,q),earlier,t.hyp('ratio'),t.hyp('head'),
            t.hyp('previous'),AndElimL(t.hyp('power_data')))
        width=apply(specialize(t,'succ_le_succ',sk,N),t.hyp('bound'))
        ratio=apply(specialize(t,'ratio',k,b,a),width,t.hyp('previous'),t.hyp('value'))
        ratio=_right(t,registry,ratio,Mul(two,a),specialize(t,'one_mul',b))
        lifted=apply(specialize(t,'mul_left_mono',Mul(two,a),b,q),ratio)
        result=apply(specialize(t,'le_trans',Mul(q,Mul(two,a)),Mul(q,b),a0),lifted,old)
        same=_chain(CongMul(AndElimR(t.hyp('power_data')),EqRefl(a)),specialize(t,'mul_assoc',q,two,a))
        return _left(t,registry,result,a0,EqSym(same))
    def successor(t):
        k,p=t.terms(('k','p'))
        power=apply(specialize(t,'power_step',two,k,Succ(k),p),EqRefl(Succ(k)),t.hyp('power'))
        return eliminate(t,power,('q',),'power_data',lambda u:
            eliminate(u,specialize(u,'beta_exists',*u.terms(A),u.term('k')),('b',),'previous',chosen))
    return Ind(target.body,introduce(s,row_parameters,row_hyps,base),
        introduce(s,('k',),('IH',),lambda t:introduce(t,row_parameters,row_hyps,successor)))


def prove_halving_prefix_decay(*,limits=None):
    registry=definition_registry();target=frozen_halving_prefix_decay_target(_registry=registry)
    return assemble_mixed_certificate(code='AP053',target=target,registry=registry,
        helper_sources={},helper_hashes={},endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'AP053':lambda s:_decay(s,target,registry)},pins=halving_prefix_decay_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=1)
