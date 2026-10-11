"""AP054: construct dyadically small finite tails for any bounded argument.

Beyond K>=2*L for x<=L*d, shift by m more terms. Construct the actual
power, heads, slice and sum, proving 2^m*head<=head[K] and
2^m*sum<=2*head[K]. No infinite remainder or exponential object is assumed.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_exp_large_argument_tail import (
    ROOT,Scope,introduce,eliminate,witness,apply,specialize,conjunction,canonical,json_hash,
    source_registry,exp_large_argument_tail_source_pins,NAMED_SOURCE as TAIL_SOURCE,
    HELPER_SOURCES as TAIL_HELPERS,ENDPOINT_SOURCES as TAIL_ENDPOINTS,
    COMPOSITION_ARCHIVE,BOUND_ARCHIVE,TAIL_ARCHIVE as SLICE_ARCHIVE,
)
from sqrt2_power_halving_prefix_decay import NAMED_SOURCE as DECAY_SOURCE,COMPARISON_ARCHIVE
from sqrt2_power_scaled_exp_tail_decay import HELPER_SOURCES as OLD_DECAY_HELPERS
from sqrt2_power_exp_truncation import DECAY_ARCHIVE as SUM_ARCHIVE
from sqrt2_power_quadratic_trace_exists import field
from sqrt2_power_log_exp_witness import conjoin
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-large-argument-decay-v1'
T,U,V=('tb','tc'),('ub','uc'),('vb','vc')
PARAMETERS=('d','x','L')+T+('K','m','N')
RECURRENCE='NatScaledExpRecurrence(d,x,tb,tc,(K+m)+N)'
PREMISES=('~d=0','Le(x,L*d)','Le(2*L,K)',RECURRENCE)
OUTPUTS=('p',)+U+('a0','a','s')
PARTS=('Pow(2,m,p)','BetaAt(tb,tc,K,a0)','BetaAt(tb,tc,K+m,a)',
    'NatAffineSlice(tb,tc,K+m,1,ub,uc,S N)','NatRatioBoundPrefix(ub,uc,1,S N)',
    'BetaAt(ub,uc,0,a)','Sum(ub,uc,S N,s)','Le(p*a,a0)','Le(p*s,2*a0)')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> exists '+' '.join(OUTPUTS)+'. '+conjoin(PARTS)
TARGET_SHA256='a11bcab301bcc1baa600ebeb7741038a4ddea68d8a679317bf9afb96a127d859'
HELPER_SOURCES={'term_decay':'forall '+' '.join(PARAMETERS+('a0','a','p'))+'. '+' -> '.join(PREMISES+
    ('BetaAt(tb,tc,K,a0)','BetaAt(tb,tc,K+m,a)','Pow(2,m,p)'))+' -> Le(p*a,a0)'}
HELPER_TARGET_SHA256={'term_decay':'4a97bffd0a6f52811ad2bfc2f7fd9e1386bdc1324540f68b569b0d1eeb04a588'}
TAIL_ARCHIVE=dict(case='AP052',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-large-argument-tail-v1/generation-process.json.gz',
    bytes=58008,sha256='265cefaa458c290a425f7ac30875af0c13ad3ac967cb079fc7124ee3e7369310',
    raw_bytes=475444,raw_sha256='47cd3ca55a654ca198a73f5151188aff1d5c01a504964ec31ab8da13d86c471f',
    bundle_bytes=220057,bundle_sha256='911984292a5e6478f05be815332b1ea99357351be9c5150149a0930b1da3293a',
    nodes=123,root=122,target_ast_sha256='bb49801153c9bc3821d1f494707843d81d2f5e20181f6172563fe79531ae95eb')
DECAY_ARCHIVE=dict(case='AP053',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-halving-prefix-decay-v1/generation-process.json.gz',
    bytes=45491,sha256='3a580d5ead9c0d855c514d84d8c39aff54db247c62a6f0731b6cc488cf359e75',
    raw_bytes=248403,raw_sha256='591a421809a493b36e10db4bb45f813abb57a2564d478a901b118dca4cd6728d',
    bundle_bytes=75671,bundle_sha256='8ab91a86da1d7a0fb5ffb4d711d6723b98695277ef3042587d475462c3bf0bbf',
    nodes=36,root=35,target_ast_sha256='07ae73101d211aba3dfdb13a23c81410079b1c0ab2cde23e58d19ff2b5e0d6d8')
ARCHIVES=(TAIL_ARCHIVE,DECAY_ARCHIVE,SLICE_ARCHIVE,SUM_ARCHIVE,COMPARISON_ARCHIVE,COMPOSITION_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'tail':TAIL_SOURCE,'decay':DECAY_SOURCE,'tail_ratio':TAIL_HELPERS['tail_ratio'],
    'tail_head':TAIL_HELPERS['tail_head'],'slice_entry':TAIL_ENDPOINTS['slice_entry'],
    'slice_exists':TAIL_ENDPOINTS['slice_exists'],'scaled_sum':OLD_DECAY_HELPERS['scaled_sum'],
    'power_exists':'forall d n. exists p. Pow(d,n,p)',
    'beta_exists':TAIL_ENDPOINTS['beta_exists'],'beta_unique':TAIL_ENDPOINTS['beta_unique'],
    'le_trans':TAIL_ENDPOINTS['le_trans'],'succ_le_succ':TAIL_ENDPOINTS['succ_le_succ'],
    'add_comm':TAIL_ENDPOINTS['add_comm'],'add_assoc':'forall a b c. (a+b)+c=a+(b+c)',
}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(tail='AP052',tail_ratio='AP052',tail_head='AP052',decay='AP053',
    slice_entry='CV087',slice_exists='CV061',scaled_sum='CV088',power_exists='AP010')
HELPER_DEPENDENCIES={
    'term_decay':('slice_exists','beta_exists','beta_unique','slice_entry','tail_ratio','tail_head',
        'decay','succ_le_succ','add_comm','add_assoc'),
    'AP054':('tail','power_exists','beta_exists','term_decay','scaled_sum','add_comm','le_trans'),
}


class ExpLargeArgumentDecayError(ValueError):
    """Changed arbitrary argument, cutoff, actual tail or dyadic error."""


def definition_registry():
    pool=source_registry();needed=set();pending=['Le','Sum','Pow','NatAffineSlice','NatRatioBoundPrefix','NatScaledExpRecurrence']
    while pending:
        name=pending.pop()
        if name not in needed:needed.add(name);pending.extend(pool[name].conceptual_dependencies)
    result={name:spec for name,spec in pool.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ExpLargeArgumentDecayError('existing large-argument decay definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_exp_large_argument_decay_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=8 or len(premises)!=4 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpLargeArgumentDecayError('AP054 exact actual large-argument decay changed')
    return target


def source_contract():
    return dict(code='AP054',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,argument_bound='x<=L*d',initial_cutoff='2*L<=K',actual_tail_start='K+m',
        actual_tail_length='N+1',actual_power_heads_slice_and_sum_constructed=True,
        finite_bounds='2^m*a<=a0; 2^m*s<=2*a0',reference_head_index='K',
        uniform_in_extra_finite_horizon=True,zero_L_K_m_N_x_and_head_allowed=True,
        new_induction_needed=False,new_induction_count=0,new_definition_ids=[],definition_admissions=0,
        infinite_tail_or_exponential_claimed=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_large_argument_decay_source_pins():
    result=exp_large_argument_tail_source_pins()
    expected={'scripts/sqrt2_power_exp_large_argument_tail.py':'66779eefe2aaafe66cc9b01f1751b842f2464a798de6334d27fb97a79afb4d8d',
        'scripts/sqrt2_power_halving_prefix_decay.py':'edc928e52e36b65e8c9ef9c06268da1c44aa6b40df7c095f2327952395dea962',**{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_large_argument_decay.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpLargeArgumentDecayError('large-argument decay source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _term_decay(s,registry):
    from peano_lab.kernel.terms import Add,Succ,Zero
    one=Succ(Zero())
    def chosen(t):
        K,m,N,a0,a,p,b=t.terms(('K','m','N','a0','a','p','b'));horizon=Add(m,N)
        width=witness((N,),specialize(t,'add_comm',N,m))
        bound=apply(specialize(t,'succ_le_succ',m,horizon),width)
        old=apply(specialize(t,'slice_entry',*t.terms(T+V),K,Succ(horizon),m,b),t.hyp('slice'),bound,t.hyp('entry'))
        same=apply(specialize(t,'beta_unique',*t.terms(T),Add(K,m),b,a),old,t.hyp('value'))
        entry=_subst(t,registry,'BetaAt(vb,vc,m,slot)',same,t.hyp('entry'))
        recurrence=_subst(t,registry,'NatScaledExpRecurrence(d,x,tb,tc,slot)',specialize(t,'add_assoc',K,m,N),t.hyp('recurrence'))
        ratio=apply(specialize(t,'tail_ratio',*t.terms(('d','x','L')+T),K,horizon,*t.terms(V)),
            t.hyp('nonzero'),t.hyp('argument'),t.hyp('threshold'),recurrence,t.hyp('slice'))
        head=apply(specialize(t,'tail_head',*t.terms(T+V),K,horizon,a0),t.hyp('slice'),t.hyp('head'))
        return apply(specialize(t,'decay',m,*t.terms(V),horizon,a0,a,p),width,ratio,head,entry,t.hyp('power'))
    def sliced(t):
        return eliminate(t,specialize(t,'beta_exists',*t.terms(V),t.term('m')),('b',),'entry',chosen)
    return introduce(s,PARAMETERS+('a0','a','p'),('nonzero','argument','threshold','recurrence','head','value','power'),lambda t:
        eliminate(t,specialize(t,'slice_exists',*t.terms(T),t.term('K'),one,Succ(Add(t.term('m'),t.term('N')))),V,'slice',sliced))


def _root(s):
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    two=Succ(Succ(Zero()))
    def chosen(t):
        tail=t.hyp('tail_data')
        decay=apply(specialize(t,'term_decay',*t.terms(PARAMETERS+('a0','a','p'))),
            *(t.hyp(n) for n in ('nonzero','argument','threshold','recurrence','head')),field(tail,2,6),t.hyp('power'))
        full=apply(specialize(t,'scaled_sum',*t.terms(('p','s','a','a0'))),decay,field(tail,5,6))
        return witness(t.terms(OUTPUTS),conjunction(t.hyp('power'),t.hyp('head'),field(tail,2,6),
            field(tail,0,6),field(tail,1,6),field(tail,3,6),field(tail,4,6),decay,full))
    def headed(t):
        K,m,L=t.terms(('K','m','L'));cutoff=Add(K,m)
        threshold=apply(specialize(t,'le_trans',Mul(two,L),K,cutoff),t.hyp('threshold'),witness((m,),specialize(t,'add_comm',m,K)))
        tail=apply(specialize(t,'tail',*t.terms(('d','x','L')+T),cutoff,t.term('N')),
            t.hyp('nonzero'),t.hyp('argument'),threshold,t.hyp('recurrence'))
        return eliminate(t,tail,U+('a','s'),'tail_data',chosen)
    return introduce(s,PARAMETERS,('nonzero','argument','threshold','recurrence'),lambda t:
        eliminate(t,specialize(t,'power_exists',two,t.term('m')),('p',),'power',lambda u:
            eliminate(u,specialize(u,'beta_exists',*u.terms(T),u.term('K')),('a0',),'head',headed)))


def prove_exp_large_argument_decay(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP054',target=frozen_exp_large_argument_decay_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'term_decay':lambda s:_term_decay(s,registry),'AP054':_root},pins=exp_large_argument_decay_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
