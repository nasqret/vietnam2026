"""AP033: an explicit finite convergence budget for the near-two witness.

Prove (n+2)*2^n <= 2*3^n and n+1 <= 3^n by ordinary HA induction.
At cutoff N=18*r+2 these give 9*r*2^N<=3^N and r<=3^(N-1).
No large numeral, matrix or exponential is materialized. This deliberately
coarse auxiliary cutoff does not change the fixed approximation program.
"""
from hashlib import sha256
import json

from sqrt2_power_positive_power_comparison import (
    ROOT,Scope,introduce,apply,specialize,canonical,json_hash,definition_registry,
    positive_power_comparison_source_pins,ENDPOINT_SOURCES as POWER_ENDPOINTS,BOUND_ARCHIVE,
)
from sqrt2_power_approximation_power_bounds import COMPARISON_ARCHIVE
from sqrt2_power_quadratic_trace_exists import eliminate,witness,conjunction
from sqrt2_power_quadratic_height import _chain,_additive_equal
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_exp_two_sided_continuity import _left,_right
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_fixed_precision_threshold import _ground_equal
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-log-exp-budget-v1"
PARTS=("~p=0","~q=0","Le(r*(9*a),p)","Le(r,q)")
NAMED_SOURCE="forall r a p q. Pow(2,S(S(18*r)),a) -> Pow(3,S(S(18*r)),p) -> Pow(3,S(18*r),q) -> "+" /\\ (".join(PARTS)+")"*(len(PARTS)-1)
TARGET_SHA256="f9b1341a43e515bdb6a1c4fc11f68e15deefecb21d6e6e05e93c1be5d19f8c43"
HELPER_SOURCES={
    "step_gap":"forall n. n+2*(S(S(S n)))=3*(S(S n))",
    "growth_gap":"forall n. (n+n+1)+S(S n)=3*(S n)",
    "step":"forall n a p. Le((S(S n))*a,2*p) -> Le((S(S(S n)))*(a*2),2*(p*3))",
    "growth_step":"forall n q. Le(S n,q) -> Le(S(S n),q*3)",
    "bernoulli":"forall n a p. Pow(2,n,a) -> Pow(3,n,p) -> Le((S(S n))*a,2*p)",
    "growth":"forall n q. Pow(3,n,q) -> Le(S n,q)",
    "cutoff":"forall r. Le(r,S(S(18*r)))",
    "budget":"forall r a p. Le((S(S(S(S(18*r)))))*a,2*p) -> Le(r*(9*a),p)",
}
HELPER_TARGET_SHA256={
    'step_gap':'0ebaf853b8d814d42115f32254f0b74037bdbe7fb47bb718d12b6501b3f125e4',
    'growth_gap':'b9809486bbd124140fb59ff0c37a1cae8f1c08d836919ee729fb2688ee1fef08',
    'step':'e3ed13390409704e4d063d657a81c4110625fb02842dab7714fe329ef2a7449d',
    'growth_step':'f30224344b4e1fc9ddc7f830eb44b193f03efa1f56740b998ba6e6ee7438cd51',
    'bernoulli':'cae5240a09d0f86cacbc899f15154b1cdd8cda53a1937d539b691b78fb555a4b',
    'growth':'51a66db78c99b883c7bdaa2c5d8e2bf029854e41455f82c08f15dd7e2d627f0b',
    'cutoff':'372c3865633c8d7e524ab94da46852b9c866ab75700fdce9515d07fd10bb4a4a',
    'budget':'420577abb3196d440cecea6d7f53c7dae34e9274ec35356c882825a72622cf8b',
}
ARCHIVES=(COMPARISON_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={name:POWER_ENDPOINTS[name] for name in ('power_zero','power_step','power_nonzero')}
ENDPOINT_SOURCES.update(
    le_refl="forall a. Le(a,a)",le_succ="forall a b. Le(a,b) -> Le(a,S b)",
    le_trans="forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    mul_left_mono="forall a b c. Le(a,b) -> Le(c*a,c*b)",mul_right_mono="forall a b c. Le(a,b) -> Le(a*c,b*c)",
    mul_le_cancel="forall c a b. ~c=0 -> Le(c*a,c*b) -> Le(a,b)",
    add_assoc="forall a b c. (a+b)+c=a+(b+c)",add_comm="forall a b. a+b=b+a",
    mul_assoc="forall a b c. (a*b)*c=a*(b*c)",mul_comm="forall a b. a*b=b*a",
    mul_succ_left="forall a b. (S a)*b=a*b+b",one_mul="forall a. 1*a=a",
    succ_ne_zero="forall a. ~S a=0")
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update({name:'AP010' for name in ('power_zero','power_step','power_nonzero')})
LINEAR=('mul_succ_left','one_mul','add_assoc','add_comm')
HELPER_DEPENDENCIES={
    'step_gap':LINEAR,'growth_gap':LINEAR,
    'step':('step_gap','mul_right_mono','mul_left_mono','le_trans','mul_assoc','mul_comm'),
    'growth_step':('growth_gap','mul_left_mono','le_trans','mul_comm'),
    'bernoulli':('power_zero','power_step','step','le_refl'),
    'growth':('power_zero','power_step','growth_step','le_refl'),
    'cutoff':('mul_succ_left','add_assoc','add_comm'),
    'budget':('le_refl','le_succ','mul_right_mono','le_trans','mul_assoc','mul_comm','mul_le_cancel','succ_ne_zero'),
    'AP033':('bernoulli','growth','cutoff','budget','power_nonzero','succ_ne_zero','le_trans'),
}
SOURCE_CLOSURE_PATH="research/arithmetic-library/sqrt2-power/observations/log-exp-budget-source-closure-v1.json"
SOURCE_CLOSURE_SHA256="a8ca7c2c99056375f5b7cb452a4e36539289546ad84c83aeed6001a1c559af75"
SOURCE_CLOSURE_BYTES=37727
SOURCE_CLOSURE_COUNT=229


class LogExpBudgetError(ValueError):
    """Changed finite power computations, explicit cutoff or source closure."""


def frozen_log_exp_budget_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=4 or len(premises)!=3 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise LogExpBudgetError('AP033 exact explicit finite convergence budget changed')
    return target


def source_contract():
    return dict(code='AP033',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=3,all_cutoff_parameters_including_zero=True,three_actual_power_computations_required=True,
        explicit_cutoff='N=18*r+2',finite_upper_budget='9*r*2^N<=3^N',finite_lower_budget='r<=3^(N-1)',
        bernoulli_inequality='(n+2)*2^n<=2*3^n',growth_inequality='n+1<=3^n',
        positive_cancel_factor_proved=True,large_ground_exponentials_materialized=False,
        fixed_approximation_program_changed=False,practical_extracted_time_claim=False,
        new_induction_needed=True,new_induction_count=2,new_definition_ids=[],definition_admissions=0,
        analytic_limit_claim=False,original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def recursive_source_pins_for_audit():
    result=positive_power_comparison_source_pins()
    expected={'scripts/sqrt2_power_fixed_precision_threshold.py':'2135396cb60dc5e367407ad5a5328066d8e252e5ca58869adbac7d370080239f',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name,digest in expected.items():
        raw=(ROOT/name).read_bytes()
        if sha256(raw).hexdigest()!=digest:
            raise LogExpBudgetError('finite budget source changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def log_exp_budget_source_pins():
    with (ROOT/SOURCE_CLOSURE_PATH).open('rb') as stream:
        raw=stream.read(SOURCE_CLOSURE_BYTES+1)
    if len(raw)!=SOURCE_CLOSURE_BYTES or sha256(raw).hexdigest()!=SOURCE_CLOSURE_SHA256:
        raise LogExpBudgetError('finite budget source closure changed')
    manifest=json.loads(raw);expected=manifest.get('source_pins',{})
    if (manifest.get('schema')!='sqrt2-power-log-exp-budget-source-closure-v1'
            or manifest.get('authority')!='source_integrity_only_not_proof_authority' or len(expected)!=SOURCE_CLOSURE_COUNT):
        raise LogExpBudgetError('finite budget source closure envelope changed')
    result={SOURCE_CLOSURE_PATH:dict(bytes=len(raw),sha256=SOURCE_CLOSURE_SHA256)}
    for name in (*expected,'scripts/sqrt2_power_log_exp_budget.py'):
        if name.startswith('/') or '..' in name.split('/'):
            raise LogExpBudgetError('finite budget source escaped repository')
        bound=expected[name]['bytes'] if name in expected else 2*1024**2
        digest=sha256();size=0
        with (ROOT/name).open('rb') as stream:
            while size<=bound:
                chunk=stream.read(min(65536,bound+1-size))
                if not chunk: break
                size+=len(chunk);digest.update(chunk)
        actual=dict(bytes=size,sha256=digest.hexdigest())
        if size>bound or name in expected and actual!=expected[name]:
            raise LogExpBudgetError('finite budget source bytes changed')
        result[name]=actual
    return result


def _linear_equal(s,left,right):
    """Tiny positive linear normalization; emit only ordinary equality terms."""
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,CongMul,CongS,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero,parse_term
    one=parse_term('1');nodes=0
    def unroll(n,v):
        if n==1: return v,specialize(s,'one_mul',v)
        prior,proof=unroll(n-1,v)
        return Add(prior,v),_chain(specialize(s,'mul_succ_left',parse_term(str(n-1)),v),CongAdd(proof,EqRefl(v)))
    def expand(term):
        nonlocal nodes
        nodes+=1
        if nodes>128: raise LogExpBudgetError('linear reconstruction structure cap exceeded')
        if term==one: return term,EqRefl(term)
        if type(term) is Succ:
            if type(term.term) is Zero: return term,EqRefl(term)
            a,p=expand(term.term)
            addone=_chain(instantiate(Axiom('PA4'),term.term,Zero()),
                CongS(instantiate(Axiom('PA3'),term.term)))
            return Add(a,one),_chain(EqSym(addone),CongAdd(p,EqRefl(one)))
        if type(term) is Add:
            a,p=expand(term.left);b,q=expand(term.right)
            return Add(a,b),CongAdd(p,q)
        if type(term) is Mul:
            n,current=0,term.left
            while type(current) is Succ and n<4: n,current=n+1,current.term
            if type(current) is not Zero or not 1<=n<=3:
                raise LogExpBudgetError('linear reconstruction permits only factors one through three')
            a,p=expand(term.right);out,q=unroll(n,a)
            return out,_chain(CongMul(EqRefl(term.left),p),q)
        return term,EqRefl(term)
    a,p=expand(left);b,q=expand(right)
    return _chain(p,_additive_equal(s,a,b),EqSym(q))


def _gap(s,name):
    from peano_lab.kernel.terms import parse_term_in_context
    left,right=HELPER_SOURCES[name].split('. ',1)[1].split('=')
    return introduce(s,('n',),(),lambda t:_linear_equal(t,
        parse_term_in_context(left,list(t.variables)),parse_term_in_context(right,list(t.variables))))


def _step(s,registry):
    from peano_lab.kernel.proofs import EqSym
    from peano_lab.kernel.terms import Mul,Succ,parse_term
    two,three=map(parse_term,('2','3'))
    def finish(t):
        n,a,p=t.terms(('n','a','p'));sn2=Succ(Succ(n));sn3=Succ(sn2)
        low=Mul(two,sn3);high=Mul(three,sn2)
        gap=witness((n,),specialize(t,'step_gap',n))
        first=apply(specialize(t,'mul_right_mono',low,high,a),gap)
        second=apply(specialize(t,'mul_left_mono',Mul(sn2,a),Mul(two,p),three),t.hyp('bound'))
        second=_left(t,registry,second,Mul(three,Mul(two,p)),EqSym(specialize(t,'mul_assoc',three,sn2,a)))
        both=apply(specialize(t,'le_trans',Mul(low,a),Mul(high,a),Mul(three,Mul(two,p))),first,second)
        both=_left(t,registry,both,Mul(three,Mul(two,p)),_multiplicative_equal(t,Mul(low,a),Mul(sn3,Mul(a,two))))
        return _right(t,registry,both,Mul(sn3,Mul(a,two)),_multiplicative_equal(t,Mul(three,Mul(two,p)),Mul(two,Mul(p,three))))
    return introduce(s,('n','a','p'),('bound',),finish)


def _growth_step(s,registry):
    from peano_lab.kernel.terms import Add,Mul,Succ,parse_term
    one,three=map(parse_term,('1','3'))
    def finish(t):
        n,q=t.terms(('n','q'));sn=Succ(n);ssn=Succ(sn)
        first=witness((Add(Add(n,n),one),),specialize(t,'growth_gap',n))
        second=apply(specialize(t,'mul_left_mono',sn,q,three),t.hyp('bound'))
        both=apply(specialize(t,'le_trans',ssn,Mul(three,sn),Mul(three,q)),first,second)
        return _right(t,registry,both,ssn,specialize(t,'mul_comm',three,q))
    return introduce(s,('n','q'),('bound',),finish)


def _bernoulli(s,target,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Mul,Succ,Zero,parse_term
    zero=Zero();one,two,three=map(parse_term,('1','2','3'))
    def base(t):
        a,p=t.terms(('a','p'))
        ae=apply(specialize(t,'power_zero',two,zero,a),EqRefl(zero),t.hyp('power_two'))
        pe=apply(specialize(t,'power_zero',three,zero,p),EqRefl(zero),t.hyp('power_three'))
        out=specialize(t,'le_refl',Mul(two,one))
        out=_left(t,registry,out,Mul(two,one),CongMul(EqRefl(two),EqSym(ae)))
        return _right(t,registry,out,Mul(two,a),CongMul(EqRefl(two),EqSym(pe)))
    def successor(t):
        def chosen(u):
            n,a,p,x,y=u.terms(('n','a','p','old_a','old_p'))
            old=apply(specialize(u,'IH',x,y),AndElimL(u.hyp('two_data')),AndElimL(u.hyp('three_data')))
            out=apply(specialize(u,'step',n,x,y),old)
            out=_left(u,registry,out,Mul(two,Mul(y,three)),CongMul(EqRefl(Succ(Succ(Succ(n)))),EqSym(AndElimR(u.hyp('two_data')))))
            return _right(u,registry,out,Mul(Succ(Succ(Succ(n))),a),CongMul(EqRefl(two),EqSym(AndElimR(u.hyp('three_data')))))
        n=t.term('n')
        first=apply(specialize(t,'power_step',two,n,Succ(n),t.term('a')),EqRefl(Succ(n)),t.hyp('power_two'))
        return eliminate(t,first,('old_a',),'two_data',lambda u:
            eliminate(u,apply(specialize(u,'power_step',three,u.term('n'),Succ(u.term('n')),u.term('p')),
                EqRefl(Succ(u.term('n'))),u.hyp('power_three')),('old_p',),'three_data',chosen))
    return Ind(target.body,introduce(s,('a','p'),('power_two','power_three'),base),
        introduce(s,('n',),('IH',),lambda t:introduce(t,('a','p'),('power_two','power_three'),successor)))


def _growth(s,target,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Mul,Succ,Zero,parse_term
    one,three=map(parse_term,('1','3'))
    def base(t):
        q=t.term('q');eq=apply(specialize(t,'power_zero',three,Zero(),q),EqRefl(Zero()),t.hyp('power'))
        return _right(t,registry,specialize(t,'le_refl',one),one,EqSym(eq))
    def chosen(t):
        n,q,p=t.terms(('n','q','old'))
        old=apply(specialize(t,'IH',p),AndElimL(t.hyp('previous')))
        result=apply(specialize(t,'growth_step',n,p),old)
        return _right(t,registry,result,Succ(Succ(n)),EqSym(AndElimR(t.hyp('previous'))))
    def successor(t):
        n=t.term('n');data=apply(specialize(t,'power_step',three,n,Succ(n),t.term('q')),EqRefl(Succ(n)),t.hyp('power'))
        return eliminate(t,data,('old',),'previous',chosen)
    return Ind(target.body,introduce(s,('q',),('power',),base),
        introduce(s,('n',),('IH',),lambda t:introduce(t,('q',),('power',),successor)))


def _cutoff(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,CongS,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero,parse_term
    two,seventeen,eighteen=map(parse_term,('2','17','18'))
    def finish(t):
        r=t.term('r');mass=Mul(seventeen,r);large=Mul(eighteen,r)
        right=_chain(instantiate(Axiom('PA4'),large,Succ(Zero())),CongS(instantiate(Axiom('PA4'),large,Zero())),
            CongS(CongS(instantiate(Axiom('PA3'),large))))
        equality=_chain(_additive_equal(t,Add(Add(mass,two),r),Add(Add(mass,r),two)),
            CongAdd(EqSym(specialize(t,'mul_succ_left',seventeen,r)),EqRefl(two)),right)
        return witness((Add(mass,two),),equality)
    return introduce(s,('r',),(),finish)


def _budget(s,registry):
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ,parse_term
    one,two,nine,eighteen=map(parse_term,('1','2','9','18'))
    def finish(t):
        r,a,p=t.terms(('r','a','p'));mass=Mul(eighteen,r);limit=mass
        bounded=specialize(t,'le_refl',mass)
        for _ in range(4):
            bounded=apply(specialize(t,'le_succ',mass,limit),bounded);limit=Succ(limit)
        bounded=apply(specialize(t,'mul_right_mono',mass,limit,a),bounded)
        bounded=apply(specialize(t,'le_trans',Mul(mass,a),Mul(limit,a),Mul(two,p)),bounded,t.hyp('bound'))
        equal=_chain(CongMul(CongMul(_ground_equal(eighteen,Mul(two,nine)),EqRefl(r)),EqRefl(a)),
            _multiplicative_equal(t,Mul(Mul(Mul(two,nine),r),a),Mul(two,Mul(r,Mul(nine,a)))))
        bounded=_left(t,registry,bounded,Mul(two,p),equal)
        return apply(specialize(t,'mul_le_cancel',two,Mul(r,Mul(nine,a)),p),specialize(t,'succ_ne_zero',one),bounded)
    return introduce(s,('r','a','p'),('bound',),finish)


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.terms import Mul,Succ,parse_term
    two,three,eighteen=map(parse_term,('2','3','18'))
    def finish(t):
        r,a,p,q=t.terms(('r','a','p','q'));index=Succ(Mul(eighteen,r));N=Succ(index)
        strong=apply(specialize(t,'bernoulli',N,a,p),t.hyp('power_two'),t.hyp('power_three'))
        upper=apply(specialize(t,'budget',r,a,p),strong)
        growth=apply(specialize(t,'growth',index,q),t.hyp('previous_three'))
        lower=apply(specialize(t,'le_trans',r,N,q),specialize(t,'cutoff',r),growth)
        nonzero=apply(specialize(t,'power_nonzero',three),specialize(t,'succ_ne_zero',two))
        pnz=apply(instantiate(nonzero,N,p),t.hyp('power_three'));qnz=apply(instantiate(nonzero,index,q),t.hyp('previous_three'))
        return conjunction(pnz,qnz,upper,lower)
    return introduce(s,('r','a','p','q'),('power_two','power_three','previous_three'),finish)


def factories(registry):
    from sqrt2_power_definitions import parse_named
    return {'step_gap':lambda s:_gap(s,'step_gap'),'growth_gap':lambda s:_gap(s,'growth_gap'),
        'step':lambda s:_step(s,registry),'growth_step':lambda s:_growth_step(s,registry),
        'bernoulli':lambda s:_bernoulli(s,parse_named(HELPER_SOURCES['bernoulli'],registry=registry),registry),
        'growth':lambda s:_growth(s,parse_named(HELPER_SOURCES['growth'],registry=registry),registry),
        'cutoff':_cutoff,'budget':lambda s:_budget(s,registry),'AP033':_root}


def prove_log_exp_budget(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP033',target=frozen_log_exp_budget_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories=factories(registry),pins=log_exp_budget_source_pins,contract=source_contract(),limits=limits,new_induction_count=2)
