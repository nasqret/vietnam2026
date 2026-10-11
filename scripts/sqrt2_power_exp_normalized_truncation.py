"""AP057: arbitrary-argument finite truncation relative to the original head.

Identify the actual term at K, majorize it by L^K*h using AP056, and retain
the caller's table, sums and powers in AP055's error bound. No positive head
or limit object is assumed.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_exp_large_argument_truncation import (
    ROOT,Scope,introduce,eliminate,witness,apply,specialize,conjunction,canonical,json_hash,
    source_registry,exp_large_argument_truncation_source_pins,NAMED_SOURCE as TRUNCATION_SOURCE,
)
from sqrt2_power_exp_geometric_majorant import NAMED_SOURCE as MAJORANT_SOURCE,BOUND_ARCHIVE
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-normalized-truncation-v1'
A=('ab','ac')
PARAMETERS=('d','x','L')+A+('K','m','N','h','s','t','p','B')
PREMISES=('~d=0','Le(x,L*d)','Le(2*L,K)','NatScaledExpRecurrence(d,x,ab,ac,(K+m)+N)',
    'BetaAt(ab,ac,0,h)','Sum(ab,ac,K+m,s)','Sum(ab,ac,S((K+m)+N),t)','Pow(2,m,p)','Pow(L,K,B)')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> Le(s,t) /\\ Le(p*t,p*s+2*(B*h))'
TARGET_SHA256='f74987c7317766d697ca0d5792985ab700e38691f10bd6149d8c1ca141fc33b9'
TRUNCATION_ARCHIVE=dict(case='AP055',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-large-argument-truncation-v1/generation-process.json.gz',
    bytes=66069,sha256='67e3fe69533b6cec03ffd83de0b671d15062e9a41bfebd8dadaa8212a8c0b9e9',
    raw_bytes=758798,raw_sha256='91cbce305770e7c75d0e1a918338567f4fb7cdc7f11d4133d1a081178a138e8f',
    bundle_bytes=396287,bundle_sha256='4b2704a69fe125f681a594b0efd0eb04b37c832be124a46f148afc31eb798a53',
    nodes=157,root=156,target_ast_sha256='6d652892aa498fb4573642b7316fc9a30f17cc0102198e2d0ca31291e5c299b0')
MAJORANT_ARCHIVE=dict(case='AP056',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-geometric-majorant-v1/generation-process.json.gz',
    bytes=47063,sha256='4dd0996634aa781db5cd8cc9639d03ffa96bf535512847f8e5a9d2f1e5ea6b53',
    raw_bytes=267285,raw_sha256='688e9dd48ca105633a577447f383aea07ac9525f48a929a944a624d5589da29f',
    bundle_bytes=87280,bundle_sha256='6d40a0ff19af1e096df1647183ec59ca894502ec46e796c50b4652362eb3ee33',
    nodes=44,root=43,target_ast_sha256='e86ad6b58635a4c4ece5af53c0cf336a09fc69caf323c09e6c79fea863077e79')
ARCHIVES=(TRUNCATION_ARCHIVE,MAJORANT_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'truncation':TRUNCATION_SOURCE,'majorant':MAJORANT_SOURCE,
    'beta_exists':'forall b c i. exists a. BetaAt(b,c,i,a)',
    'add_comm':'forall a b. a+b=b+a','le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'add_left_mono':'forall a b c. Le(a,b) -> Le(c+a,c+b)',
}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(truncation='AP055',majorant='AP056')
HELPER_DEPENDENCIES={'AP057':tuple(ENDPOINT_SOURCES)}


class ExpNormalizedTruncationError(ValueError):
    """Changed original normalization, actual sums, powers or error bound."""


def definition_registry():
    pool=source_registry();needed=set();pending=['Le','Sum','Pow','NatScaledExpRecurrence']
    while pending:
        name=pending.pop()
        if name not in needed:needed.add(name);pending.extend(pool[name].conceptual_dependencies)
    result={name:spec for name,spec in pool.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ExpNormalizedTruncationError('existing normalized-truncation definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_exp_normalized_truncation_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=13 or len(premises)!=9 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpNormalizedTruncationError('AP057 exact original-head truncation changed')
    return target


def source_contract():
    return dict(code='AP057',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=9,supplied_table_original_head_sums_and_both_powers_preserved=True,
        argument_bound='x<=L*d',initial_cutoff='2*L<=K',reference_head_index=0,
        prefix_length='K+m',whole_length='K+m+N+1',actual_reference_term_decoded=True,
        finite_bounds='s<=t; p*t<=p*s+2*(B*h)',powers='p=2^m; B=L^K',
        uniform_in_extra_finite_horizon=True,zero_head_and_empty_prefix_allowed=True,
        new_induction_needed=False,new_induction_count=0,new_definition_ids=[],definition_admissions=0,
        infinite_tail_or_exponential_claimed=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_normalized_truncation_source_pins():
    result=exp_large_argument_truncation_source_pins()
    expected={'scripts/sqrt2_power_exp_large_argument_truncation.py':'0b1febb190441c5262f4fd787d684ee7aebb507cf014fb729f86395ae96a17e3',
        'scripts/sqrt2_power_exp_geometric_majorant.py':'8a60b2ce82d2219c980e03e96cbbc663fdd62334da4348bbc15efe09fad75477',**{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_normalized_truncation.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpNormalizedTruncationError('normalized truncation source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _root(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    two=Succ(Succ(Zero()))
    def chosen(t):
        d,x,L,K,m,N,h,z,out,p,B,a0=t.terms(('d','x','L','K','m','N','h','s','t','p','B','a0'))
        cutoff=Add(K,m);degree=Add(cutoff,N)
        width=apply(specialize(t,'le_trans',K,cutoff,degree),
            witness((m,),specialize(t,'add_comm',m,K)),witness((N,),specialize(t,'add_comm',N,cutoff)))
        majorant=apply(specialize(t,'majorant',K,d,x,L,*t.terms(A),degree,h,a0,B),t.hyp('nonzero'),t.hyp('argument'),
            width,t.hyp('recurrence'),t.hyp('head'),t.hyp('reference'),t.hyp('majorant_power'))
        error=apply(specialize(t,'truncation',d,x,L,*t.terms(A),K,m,N,a0,z,out,p),
            *(t.hyp(n) for n in ('nonzero','argument','threshold','recurrence','reference','prefix','whole','power')))
        old_error=Mul(two,a0);new_error=Mul(two,Mul(B,h));short=Mul(p,z)
        lifted=apply(specialize(t,'mul_left_mono',a0,Mul(B,h),two),majorant)
        lifted=apply(specialize(t,'add_left_mono',old_error,new_error,short),lifted)
        bound=apply(specialize(t,'le_trans',Mul(p,out),Add(short,old_error),Add(short,new_error)),AndElimR(error),lifted)
        return conjunction(AndElimL(error),bound)
    return introduce(s,PARAMETERS,('nonzero','argument','threshold','recurrence','head','prefix','whole','power','majorant_power'),lambda t:
        eliminate(t,specialize(t,'beta_exists',*t.terms(A),t.term('K')),('a0',),'reference',chosen))


def prove_exp_normalized_truncation(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP057',target=frozen_exp_normalized_truncation_target(_registry=registry),registry=registry,
        helper_sources={},helper_hashes={},endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'AP057':_root},pins=exp_normalized_truncation_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
