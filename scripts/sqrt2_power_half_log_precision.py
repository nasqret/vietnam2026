"""AP046: the actual half-logarithm cutoff power dominates its error scale.

Ordinary induction proves n+1<=2^n for supplied power computations. The
existing 18*r+2 cutoff comparison then yields r<=2^(18*r+2), including r=0.
No exponentially large ground numeral is generated or trusted.
"""
from hashlib import sha256

from sqrt2_power_log_exp_budget import (
    ROOT,Scope,introduce,eliminate,witness,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,log_exp_budget_source_pins,
    HELPER_SOURCES as BUDGET_HELPERS,COMPARISON_ARCHIVE,BOUND_ARCHIVE,
)
from sqrt2_power_log_exp_dyadic_witness import BUDGET_ARCHIVE
from sqrt2_power_exp_two_sided_continuity import _right
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-half-log-precision-v1'
NAMED_SOURCE='forall r p. Pow(2,S(S(18*r)),p) -> ~p=0 /\\ Le(r,p)'
TARGET_SHA256='936a988b2a6fae61ebb3206a2a33746d5c8ad2e23501f642b0528b6b9e0e7877'
HELPER_SOURCES={'step_gap':'forall n. n+S(S n)=(S n)*2',
    'step':'forall n p. Le(S n,p) -> Le(S(S n),p*2)',
    'growth':'forall n p. Pow(2,n,p) -> Le(S n,p)'}
HELPER_TARGET_SHA256={'step_gap':'201e88f196a3a14c0938283ec59c04d15dc398f6ad236a243998dc5d3ee430f8',
    'step':'6b6168bbf501831e9121cd2845b61ebd7ece1f83cc4f89e5edf3731db270f596',
    'growth':'2cc4d957ed4e00cbafea89772352561653a97a6a3c5fc2123ee83053d077e565'}
ARCHIVES=(BUDGET_ARCHIVE,COMPARISON_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={
    'cutoff':BUDGET_HELPERS['cutoff'],
    'power_zero':'forall d n p. n=0 -> Pow(d,n,p) -> p=1',
    'power_step':'forall d n sn p. sn=S n -> Pow(d,sn,p) -> exists q. Pow(d,n,q) /\\ p=q*d',
    'power_nonzero':'forall a. ~a=0 -> forall k p. Pow(a,k,p) -> ~p=0',
    'le_refl':'forall a. Le(a,a)','le_succ':'forall a b. Le(a,b) -> Le(a,S b)',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'succ_ne_zero':'forall a. ~S a=0',
    'mul_right_mono':'forall a b c. Le(a,b) -> Le(a*c,b*c)',
    'add_succ_left':'forall a b. S a+b=S(a+b)',
    'mul_succ_left':'forall a b. (S a)*b=a*b+b',
    'one_mul':'forall a. 1*a=a','mul_comm':'forall a b. a*b=b*a',
}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(cutoff='AP033',power_zero='AP010',power_step='AP010',power_nonzero='AP010')
HELPER_DEPENDENCIES={'step_gap':('add_succ_left','mul_succ_left','one_mul','mul_comm'),
    'step':('step_gap','mul_right_mono','le_trans'),
    'growth':('power_zero','power_step','le_refl','step'),
    'AP046':('growth','cutoff','le_refl','le_succ','le_trans','power_nonzero','succ_ne_zero')}


class HalfLogPrecisionError(ValueError):
    """Changed supplied cutoff power, explicit degree or natural scale order."""


def frozen_half_log_precision_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=2 or len(premises)!=1 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise HalfLogPrecisionError('AP046 exact finite half-log precision domination changed')
    return target


def source_contract():
    return dict(code='AP046',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,actual_supplied_power_required=True,degree='18*r+2',power='2^(18*r+2)',
        supplied_power_proved_nonzero=True,precision_domination='r<=p',zero_scale_allowed=True,
        generic_binary_growth='n+1<=2^n',large_ground_power_materialized=False,
        new_induction_needed=True,new_induction_count=1,new_definition_ids=[],definition_admissions=0,
        analytic_limit_claim=False,original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def half_log_precision_source_pins():
    result=log_exp_budget_source_pins()
    expected={'scripts/sqrt2_power_log_exp_budget.py':'d312576300489ff9d35d655060d9d9056d7e8e7c79b491f312ce6f0347e57be0',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_half_log_precision.py'):
        with (ROOT/name).open('rb') as stream: raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise HalfLogPrecisionError('half-log precision source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _step_gap(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Succ,Zero
    def finish(t):
        n=t.term('n');sn=Succ(n);one=Succ(Zero());two=Succ(one)
        double=_chain(specialize(t,'mul_succ_left',one,sn),CongAdd(specialize(t,'one_mul',sn),EqRefl(sn)))
        return _chain(instantiate(Axiom('PA4'),n,sn),EqSym(specialize(t,'add_succ_left',n,sn)),EqSym(double),specialize(t,'mul_comm',two,sn))
    return introduce(s,('n',),(),finish)


def _step(s):
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def finish(t):
        n,p=t.terms(('n','p'));sn=Succ(n);ssn=Succ(sn);two=Succ(Succ(Zero()))
        below=witness((n,),specialize(t,'step_gap',n))
        above=apply(specialize(t,'mul_right_mono',sn,p,two),t.hyp('bound'))
        return apply(specialize(t,'le_trans',ssn,Mul(sn,two),Mul(p,two)),below,above)
    return introduce(s,('n','p'),('bound',),finish)


def _growth(s,target,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Succ,Zero
    zero=Zero();one=Succ(zero);two=Succ(one)
    def base(t):
        p=t.term('p');same=apply(specialize(t,'power_zero',two,zero,p),EqRefl(zero),t.hyp('power'))
        return _right(t,registry,specialize(t,'le_refl',one),one,EqSym(same))
    def chosen(t):
        n,q=t.terms(('n','q'));data=t.hyp('previous')
        old=apply(specialize(t,'IH',q),AndElimL(data))
        result=apply(specialize(t,'step',n,q),old)
        return _right(t,registry,result,Succ(Succ(n)),EqSym(AndElimR(data)))
    def successor(t):
        n,p=t.terms(('n','p'))
        data=apply(specialize(t,'power_step',two,n,Succ(n),p),EqRefl(Succ(n)),t.hyp('power'))
        return eliminate(t,data,('q',),'previous',chosen)
    return Ind(target.body,introduce(s,('p',),('power',),base),
        introduce(s,('n',),('IH',),lambda t:introduce(t,('p',),('power',),successor)))


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.terms import Mul,Succ,Zero,parse_term
    def finish(t):
        r,p=t.terms(('r','p'));one=Succ(Zero());two=Succ(one);M=Succ(Succ(Mul(parse_term('18'),r)))
        nz=apply(instantiate(apply(specialize(t,'power_nonzero',two),specialize(t,'succ_ne_zero',one)),M,p),t.hyp('power'))
        growth=apply(specialize(t,'growth',M,p),t.hyp('power'))
        predecessor=apply(specialize(t,'le_succ',M,M),specialize(t,'le_refl',M))
        growth=apply(specialize(t,'le_trans',M,Succ(M),p),predecessor,growth)
        bound=apply(specialize(t,'le_trans',r,M,p),specialize(t,'cutoff',r),growth)
        return conjunction(nz,bound)
    return introduce(s,('r','p'),('power',),finish)


def prove_half_log_precision(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry=definition_registry();growth=parse_named(HELPER_SOURCES['growth'],registry=registry)
    return assemble_mixed_certificate(code='AP046',target=frozen_half_log_precision_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'step_gap':_step_gap,'step':_step,'growth':lambda s:_growth(s,growth,registry),'AP046':_root},
        pins=half_log_precision_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
