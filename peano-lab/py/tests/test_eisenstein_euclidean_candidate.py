"""Non-admitting original-kernel and independent semantic Eisenstein checks.

The exact v27 JSON catalogue supplies only hypotheses for curried body checks.
Actual closed dependency replay and Lean admission are separate release gates.
"""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
from itertools import product
from math import isqrt
import re

import pytest

from peano_lab.kernel.formulas import And, Bot, Eq, Exists, Forall, Imp, parse_formula_in_context, parse_formula_with_names
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero
from peano_lab.library import eisenstein_euclidean_candidate as candidate
from peano_lab.library import gaussian_euclidean_candidate as gaussian
from peano_lab.library.gaussian_euclidean_candidate import make_gaussian_euclidean_candidate_theorems
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula

from test_signed_integer_division_candidate import core as parent_core, rows as division_rows


@lru_cache(maxsize=1)
def core():
    result = dict(parent_core())
    for row in (*division_rows(),*make_gaussian_euclidean_candidate_theorems(TheoremSpec)):
        assert row.name not in result
        result[row.name] = row
    assert len(result)==2560+5+88
    return result


@lru_cache(maxsize=1)
def rows():
    return candidate.make_eisenstein_euclidean_candidate_theorems(TheoremSpec)


PRINCIPAL_NAMES=(
    'eisenstein_signed_euclidean_division_exists',
    'eisenstein_norm_exists_unique',
    'eisenstein_add_exists',
    'eisenstein_multiply_exists',
    'eisenstein_norm_multiply',
    'eisenstein_euclidean_division_exists',
)
ROOT_PINS={
    'eisenstein_signed_euclidean_division_exists':'481e8a8d2b7dc8431901e86b902b578a144c8aa72133a5e5e6b4b6c8c5e44725',
    'eisenstein_norm_exists_unique':'d714c36818ece61df74c00ba98e1ee8d42088fbc02faccfcefb4cf053e39c1b5',
    'eisenstein_add_exists':'d4eef68809aa569e91530014909f8b0f27df7cb44d02d499c43403b89cbef319',
    'eisenstein_multiply_exists':'06cca39ddb2e8b5d18210bf0ed9a24e36653bee25af58920a1ac1cca363ab482',
    'eisenstein_norm_multiply':'42d3bea19f1c39be902a69da5b51c89dc4acef875a41d63dc46d20eef932e340',
    'eisenstein_euclidean_division_exists':'160d72250ab01db0ed32ca57bc472fd22d5ea307e4042815397cc771c3e102a9',
}


EXPECTED_BODY_METRICS={
    'eisenstein_natural_norm_symmetric':(17,12,17),
    'eisenstein_natural_norm_gap_value':(176,51,157),
    'eisenstein_natural_norm_exists':(250,45,226),
    'eisenstein_natural_norm_zero':(294,30,293),
    'eisenstein_natural_norm_le_larger_square':(52,22,52),
    'eisenstein_parallelogram_norm_strict':(122,40,122),
    'eisenstein_coordinate_norm_functional':(27,19,27),
    'eisenstein_coordinate_norm_negation':(455,65,387),
    'eisenstein_normal_coordinate_norm_exists':(463,46,388),
    'eisenstein_pair_natural_value_transport':(61,30,59),
    'eisenstein_coordinate_norm_transport':(92,32,92),
    'eisenstein_coordinate_norm_exists':(76,30,76),
    'eisenstein_norm_square_balance':(473,66,406),
    'eisenstein_weighted_embedding_compensation':(1242,75,1121),
    'eisenstein_norm_weighted_square_identity':(141,34,141),
    'eisenstein_weighted_norm_exists':(21,13,21),
    'eisenstein_weighted_norm_functional':(53,24,53),
    'eisenstein_norm_to_weighted_norm':(44,29,44),
    'eisenstein_weighted_norm_transport':(88,40,88),
    'eisenstein_weighted_norm_scaled':(164,47,153),
    'eisenstein_signed_product_scaled_right':(112,27,102),
    'eisenstein_weighted_lagrange_compensation':(184,49,184),
    'eisenstein_weighted_square_lagrange':(70,40,70),
    'eisenstein_weighted_norm_product':(361,75,361),
    'eisenstein_real_associate_left_positive':(737,76,642),
    'eisenstein_real_associate_left_negative':(737,76,642),
    'eisenstein_real_associate_right_positive':(469,55,412),
    'eisenstein_real_associate_right_negative':(469,55,412),
    'eisenstein_product_associate_real':(123,37,123),
    'eisenstein_product_difference_real_positive':(139,33,130),
    'eisenstein_product_difference_real_negative':(139,33,130),
    'eisenstein_product_difference_imaginary_positive':(262,41,243),
    'eisenstein_product_difference_imaginary_negative':(262,41,243),
    'eisenstein_product_difference':(73,32,73),
    'eisenstein_product_integer_congruence':(142,37,142),
    'eisenstein_omega_product_covariance':(795,52,746),
    'eisenstein_product_associate_imaginary':(119,44,119),
    'eisenstein_product_associate':(113,40,113),
    'eisenstein_coordinate_norm_conjugate':(929,65,888),
    'eisenstein_conjugate_product_is_norm':(643,42,643),
    'eisenstein_natural_scalar_product':(138,31,109),
    'eisenstein_adjoint_product_is_norm_scale':(108,39,108),
    'eisenstein_residual_conjugate_identity':(242,97,242),
    'eisenstein_product_commute':(476,36,456),
    'eisenstein_product_conjugate':(1146,54,1083),
    'eisenstein_product_shuffle':(259,48,259),
    'eisenstein_coordinate_norm_product':(360,57,326),
    'eisenstein_coordinate_norm_zero':(174,32,169),
    'eisenstein_coordinate_norm_nonzero':(35,22,35),
    'eisenstein_natural_norm_coordinates':(79,27,65),
    'eisenstein_signed_euclidean_division_exists':(281,71,278),
    'eisenstein_norm_of_representation':(15,14,15),
    'eisenstein_norm_for_representation':(65,30,65),
    'eisenstein_norm_exists':(38,20,38),
    'eisenstein_norm_functional':(80,43,80),
    'eisenstein_norm_exists_unique':(22,15,22),
    'eisenstein_add_exists':(2,2,2),
    'eisenstein_add_functional':(2,2,2),
    'eisenstein_multiply_of_representations':(27,25,27),
    'eisenstein_multiply_for_representations':(238,108,238),
    'eisenstein_multiply_exists':(62,32,62),
    'eisenstein_multiply_functional':(119,63,119),
    'eisenstein_norm_multiply':(172,77,172),
    'eisenstein_division_remainder_of_representations':(97,48,97),
    'eisenstein_euclidean_division_exists':(180,62,180),
}


@pytest.mark.parametrize('name',tuple(row.name for row in rows()))
def test_original_kernel_bodies(name):
    table={row.name:row for row in rows()}
    try:
        receipt=replay_candidate_bodies((table[name],),core=core()|table)[0]
        assert receipt.name==name and receipt.proof_depth<=256
        assert (receipt.proof_nodes,receipt.proof_depth,receipt.proof_objects)==EXPECTED_BODY_METRICS[name]
        assert receipt.proof_objects<=receipt.proof_nodes
        assert receipt.proof_edges==receipt.proof_nodes-1
        print(f'{name}:{receipt.proof_nodes}/{receipt.proof_depth}/{receipt.proof_objects}')
    finally:
        gc.collect()


def test_inventory_is_fresh_ordered_and_constructive_over_only_the_pinned_basis():
    available=set(core())
    names=tuple(row.name for row in rows())
    assert names==tuple(EXPECTED_BODY_METRICS)
    assert sum(value[0] for value in EXPECTED_BODY_METRICS.values())==15606
    assert sum(value[2] for value in EXPECTED_BODY_METRICS.values())==14590
    assert max(value[0] for value in EXPECTED_BODY_METRICS.values())==1242
    assert max(value[1] for value in EXPECTED_BODY_METRICS.values())==108
    assert len(names)==65
    assert sum(len(row.dependencies) for row in rows())==308
    assert sum(len(row.script) for row in rows())==5414
    assert sha256('\n'.join(names).encode()).hexdigest()=='84418d12592edad52cb6f87ccc0904fdca5cafb8c75bc17c487f8599e9348854'
    assert set(PRINCIPAL_NAMES)<=set(names)
    for row in rows():
        assert row.name not in available
        assert set(row.dependencies)<=available
        assert len(row.dependencies)==len(set(row.dependencies))
        assert all(re.search(r"(?<![\w'])"+re.escape(dep)+r"(?![\w'])",'\n'.join(row.script)) for dep in row.dependencies)
        assert not any(command.startswith(('use ','admit','sorry','DNE','ring')) for command in row.script)
        assert 'gaussian_euclidean_division_exists' not in row.dependencies
        assert 'gaussian_signed_euclidean_division_exists' not in row.dependencies
        _closed_formula(row.statement)
        available.add(row.name)


@pytest.mark.parametrize('name',PRINCIPAL_NAMES)
def test_principal_statement_identities_are_independently_pinned(name):
    row=next(row for row in rows() if row.name==name)
    assert sha256(row.statement.encode()).hexdigest()==ROOT_PINS[name]


@pytest.mark.parametrize('name',tuple(row.name for row in rows()))
def test_poisoned_body_is_rejected_by_the_unchanged_kernel(name):
    table={row.name:row for row in rows()}
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(table[name],script=('exact missing_eisenstein_oracle',)),),core=core()|table)
    gc.collect()


@pytest.mark.parametrize('name',PRINCIPAL_NAMES)
def test_false_principal_conclusions_and_missing_dependencies_are_rejected(name):
    table={row.name:row for row in rows()}
    for changed in (
        replace(table[name],statement=f'({table[name].statement}) /\\ false'),
        replace(table[name],dependencies=table[name].dependencies[1:]),
    ):
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((changed,),core=core()|table)
    gc.collect()


def _both(*parts):
    result=f'({parts[-1]})'
    for part in reversed(parts[:-1]):
        result=f'({part}) /\\ ({result})'
    return result


def _plus(a,b):
    return f'(({a})+({b}))'


def _times(a,b):
    return f'(({a})*({b}))'


def _reference_sd(code,p,n,tag):
    k='audit_half_'+tag
    return f'(({code})=2*({p}) /\\ ({n})=0) \\/ exists {k}. ((({code})=2*{k}+1 /\\ ({p})=0) /\\ ({n})=S {k})'


def _reference_balance(code,p,n,tag):
    u,v='audit_p_'+tag,'audit_n_'+tag
    return f'exists {u} {v}. '+_both(_reference_sd(code,u,v,tag+'decode'),f'({p})+{v}=({n})+{u}')


def _reference_rep(code,A,tag,*,normalized=False):
    rc,ic='audit_real_'+tag,'audit_imaginary_'+tag
    graph=_reference_sd if normalized else _reference_balance
    return f'exists {rc} {ic}. '+_both(f'({code})=({rc}+{ic})*S({rc}+{ic})+({ic}+{ic})',graph(rc,*A[:2],tag+'real'),graph(ic,*A[2:],tag+'imaginary'))


def _reference_valid(code,tag):
    A=tuple('audit_valid_'+label+'_'+tag for label in ('rp','rn','ip','in'))
    return f'exists {" ".join(A)}. ({_reference_rep(code,A,tag+"decode",normalized=True)})'


def _reference_norm_raw(A,N):
    p,n,q,m=A
    positive=_plus(_plus(_plus(_times(p,p),_times(n,n)),_plus(_times(q,q),_times(m,m))),_plus(_times(p,m),_times(n,q)))
    negative=_plus(_plus(_plus(_times(p,n),_times(n,p)),_plus(_times(q,m),_times(m,q))),_plus(_times(p,q),_times(n,m)))
    return f'{positive}={_plus(negative,N)}'


def _reference_norm(code,N,tag):
    A=tuple('audit_norm_'+label+'_'+tag for label in ('rp','rn','ip','in'))
    return f'exists {" ".join(A)}. '+_both(_reference_rep(code,A,tag+'representation'),_reference_norm_raw(A,N))


def _reference_product(A,B):
    p,n,q,m=A
    u,v,w,x=B
    acp,acn=_plus(_times(p,u),_times(n,v)),_plus(_times(p,v),_times(n,u))
    bdp,bdn=_plus(_times(q,w),_times(m,x)),_plus(_times(q,x),_times(m,w))
    adp,adn=_plus(_times(p,w),_times(n,x)),_plus(_times(p,x),_times(n,w))
    bcp,bcn=_plus(_times(q,u),_times(m,v)),_plus(_times(q,v),_times(m,u))
    return _plus(acp,bdn),_plus(acn,bdp),_plus(_plus(adp,bcp),bdn),_plus(_plus(adn,bcn),bdp)


def _reference_operation(a,b,c,tag,*,multiply):
    A=tuple('audit_first_'+label+'_'+tag for label in ('rp','rn','ip','in'))
    B=tuple('audit_second_'+label+'_'+tag for label in ('rp','rn','ip','in'))
    C=_reference_product(A,B) if multiply else tuple(_plus(x,y) for x,y in zip(A,B,strict=True))
    return f'exists {" ".join((*A,*B))}. '+_both(_reference_rep(a,A,tag+'first'),_reference_rep(b,B,tag+'second'),_reference_rep(c,C,tag+'result'))


def _reference_divrem(a,b,q,r,tag):
    value='audit_product_'+tag
    return f'exists {value}. '+_both(_reference_operation(b,q,value,tag+'mul',multiply=True),_reference_operation(value,r,a,tag+'add',multiply=False))


def _reference_euclidean(a,b,q,r,U,V,tag):
    return _both(_reference_divrem(a,b,q,r,tag+'equation'),_reference_norm(r,U,tag+'smallnorm'),_reference_norm(b,V,tag+'largenorm'),f'exists audit_gap_{tag}. audit_gap_{tag}+S({U})=({V})')


def _same_formula(actual,expected,variables):
    assert parse_formula_in_context(actual,list(variables))==parse_formula_in_context(expected,list(variables))


def test_code_carrier_and_addition_are_exact_shared_ZPair_relations():
    _same_formula(candidate.eisenstein_integer_relation('z',tag='eis',variables=('z',)),gaussian.gaussian_integer_relation('z',tag='gauss'),('z',))
    _same_formula(candidate.eisenstein_add_relation('a','b','c',tag='eis',variables=('a','b','c')),gaussian.gaussian_add_relation('a','b','c',tag='gauss'),('a','b','c'))
    _same_formula(candidate.eisenstein_integer_relation('z',tag='eis',variables=('z',)),_reference_valid('z','independent'),('z',))


def test_norm_product_and_divrem_are_exact_independent_Eisenstein_graphs():
    _same_formula(candidate.eisenstein_norm_relation('z','N',tag='norm',variables=('z','N')),_reference_norm('z','N','audit'),('z','N'))
    eis=candidate.eisenstein_multiply_relation('a','b','c',tag='mul',variables=('a','b','c'))
    _same_formula(eis,_reference_operation('a','b','c','audit',multiply=True),('a','b','c'))
    assert parse_formula_in_context(eis,['a','b','c'])!=parse_formula_in_context(gaussian.gaussian_multiply_relation('a','b','c',tag='different_ring'),['a','b','c'])
    _same_formula(candidate.eisenstein_division_remainder_relation('a','b','q','r',tag='division',variables=('a','b','q','r')),_reference_divrem('a','b','q','r','audit'),('a','b','q','r'))
    args=('a','b','q','r','U','V')
    _same_formula(candidate.eisenstein_euclidean_division_relation(*args,tag='euclidean',variables=args),_reference_euclidean(*args,'audit'),args)


def test_primitive_coordinate_relations_accept_actual_compound_terms_in_declared_context():
    variables=('a','b','c','d','N')
    coords=('a+1','b*b','c+2','d+d')
    source=candidate.eisenstein_coordinate_norm_relation(*coords,'N+N',tag='norm',variables=variables)
    _same_formula(source,_reference_norm_raw(coords,'N+N'),variables)
    A,B,C=('a+1','b*b','c+2','d+d'),('N','0','a+b','1'),('a+c','b+d','N+1','0')
    P=_reference_product(A,B)
    expected=_both(f'{_plus(P[0],C[1])}={_plus(C[0],P[1])}',f'{_plus(P[2],C[3])}={_plus(C[2],P[3])}')
    _same_formula(candidate.eisenstein_coordinate_product_relation(*A,*B,*C,tag='product',variables=variables),expected,variables)


def test_code_relations_also_preserve_compound_argument_terms_without_text_substitution():
    context=('a','b','q','r','U','V')
    _same_formula(candidate.eisenstein_norm_relation('a+b','U*U',tag='compound',variables=context),_reference_norm('a+b','U*U','audit'),context)
    args=('a+b','b*b','q+1','r+r','U*U','V+1')
    _same_formula(candidate.eisenstein_euclidean_division_relation(*args,tag='compound',variables=context),_reference_euclidean(*args,'audit'),context)


def test_full_canonical_endpoint_assumes_only_valid_inputs_and_nonzero_divisor():
    expected=f"forall a b. ({_reference_valid('a','first')}) -> ({_reference_valid('b','second')}) -> ~(b=0) -> exists q r U V. ({_reference_euclidean('a','b','q','r','U','V','answer')})"
    actual=next(row.statement for row in rows() if row.name=='eisenstein_euclidean_division_exists')
    assert _closed_formula(actual)==_closed_formula(expected)
    result=_closed_formula(actual)
    assert type(result) is Forall and type(result.body) is Forall
    body=result.body.body
    assert type(body) is Imp and type(body.left) is Exists
    assert type(body.right) is Imp and type(body.right.left) is Exists
    assert body.right.right.left==Imp(Eq(Var(0),Zero()),Bot())
    body=body.right.right.right
    for _ in range(4):
        assert type(body) is Exists
        body=body.body
    assert type(body) is And


def test_raw_endpoint_has_actual_norms_and_equation_with_no_floor_or_bound_premise():
    A,B,Q,R=('a','b','c','d'),('e','f','g','h'),('qp','qn','ip','in'),('rp','rn','sp','sn')
    P=_reference_product(B,Q)
    total=tuple(_plus(x,y) for x,y in zip(P,R,strict=True))
    equation=_both(f'{_plus(total[0],A[1])}={_plus(A[0],total[1])}',f'{_plus(total[2],A[3])}={_plus(A[2],total[3])}')
    answer=_both(equation,_reference_norm_raw(R,'U'),_reference_norm_raw(B,'V'),'exists gap. gap+S U=V')
    expected=f"forall {' '.join((*A,*B))}. ~(e=f /\\ g=h) -> exists {' '.join((*Q,*R,'U','V'))}. ({answer})"
    actual=next(row.statement for row in rows() if row.name=='eisenstein_signed_euclidean_division_exists')
    assert _closed_formula(actual)==_closed_formula(expected)
    args=(*A,*B,*Q,*R,'U','V')
    _same_formula(candidate.eisenstein_signed_division_remainder_relation(*args,tag='raw',variables=args),answer,args)


@pytest.mark.parametrize('name,guard',(
    ('eisenstein_euclidean_division_exists','~(bc = 0) -> '),
    ('eisenstein_signed_euclidean_division_exists','~(e = f /\\ g = h) -> '),
))
def test_nonzero_divisor_guard_cannot_be_deleted_from_the_actual_proof(name,guard):
    table={row.name:row for row in rows()}
    changed=replace(table[name],statement=table[name].statement.replace(guard,'',1))
    assert changed.statement!=table[name].statement
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,),core=core()|table)
    gc.collect()


SURFACES=(
    (candidate.eisenstein_coordinate_norm_relation,('a','b','c','d','N')),
    (candidate.eisenstein_coordinate_product_relation,tuple('v'+str(i) for i in range(12))),
    (candidate.eisenstein_integer_relation,('z',)),
    (candidate.eisenstein_add_relation,('a','b','c')),
    (candidate.eisenstein_norm_relation,('z','N')),
    (candidate.eisenstein_multiply_relation,('a','b','c')),
    (candidate.eisenstein_division_remainder_relation,('a','b','q','r')),
    (candidate.eisenstein_euclidean_division_relation,('a','b','q','r','U','V')),
    (candidate.eisenstein_signed_division_remainder_relation,tuple('v'+str(i) for i in range(18))),
)


@pytest.mark.parametrize('builder,args',SURFACES)
def test_surfaces_are_hygienic_alpha_equivalent_and_have_only_declared_free_variables(builder,args):
    first,names=parse_formula_with_names(builder(*args,tag='first',variables=args))
    second,other_names=parse_formula_with_names(builder(*args,tag='second',variables=args))
    assert first==second and names==other_names
    assert set(names)==set(args)


@pytest.mark.parametrize('builder,args',SURFACES)
@pytest.mark.parametrize('bad',('','unknown','a-b','a/b','exists k. k','a=0','x) -> false',None,17))
def test_surfaces_reject_undeclared_or_nonterm_arguments(builder,args,bad):
    with pytest.raises((ValueError,TypeError)):
        builder(bad,*args[1:],tag='audit',variables=args)


@pytest.mark.parametrize('builder,args',SURFACES)
@pytest.mark.parametrize('context',((),('x','x'),('forall',),('x',[]),['x']))
def test_surfaces_require_explicit_valid_identifier_contexts(builder,args,context):
    with pytest.raises((ValueError,TypeError)):
        builder(*args,tag='audit',variables=context)


@pytest.mark.parametrize('builder,args',SURFACES)
@pytest.mark.parametrize('bad',('','S','forall','bad tag','x) -> false',None,17))
def test_surfaces_validate_even_unused_binder_tags(builder,args,bad):
    with pytest.raises(ValueError):
        builder(*args,tag=bad,variables=args)


@pytest.mark.parametrize('builder,args',SURFACES[2:])
@pytest.mark.parametrize('prefix',('ee_','ge_','sd_','sb_','sif_'))
def test_coded_surfaces_prevent_new_and_shared_binder_capture(builder,args,prefix):
    variables=(*args,prefix+'capture')
    with pytest.raises(ValueError,match='capture'):
        builder(*args,tag='audit',variables=variables)


def _term_value(term,values):
    if type(term) is Var:
        return values[term.index]
    if type(term) is Zero:
        return 0
    if type(term) is Succ:
        return _term_value(term.term,values)+1
    if type(term) is Add:
        return _term_value(term.left,values)+_term_value(term.right,values)
    if type(term) is Mul:
        return _term_value(term.left,values)*_term_value(term.right,values)
    raise AssertionError('foreign arithmetic term in the conservative relation')


def _quantifier_free_value(formula,values):
    if type(formula) is Eq:
        return _term_value(formula.left,values)==_term_value(formula.right,values)
    if type(formula) is And:
        return _quantifier_free_value(formula.left,values) and _quantifier_free_value(formula.right,values)
    raise AssertionError('the raw polynomial graph contains an unexpected logical operator')


def _enorm(A):
    a,b=A
    return a*a-a*b+b*b


def _emul(A,B):
    a,b=A
    c,d=B
    return a*c-b*d,a*d+b*c-b*d


def _conj(A):
    return A[0]-A[1],-A[1]


def _represented(A):
    return A[0]-A[1],A[2]-A[3]


def _raw(A,padding=0):
    return max(A[0],0)+padding,max(-A[0],0)+padding,max(A[1],0)+padding,max(-A[1],0)+padding


def test_actual_norm_polynomial_covers_zero_all_signs_and_overlapping_representatives():
    context=('a','b','c','d','N')
    formula=parse_formula_in_context(candidate.eisenstein_coordinate_norm_relation(*context,tag='audit',variables=context),list(context))
    for coords in product(range(6),repeat=4):
        N=_enorm(_represented(coords))
        assert N>=0
        assert _quantifier_free_value(formula,(*coords,N))
        assert not _quantifier_free_value(formula,(*coords,N+1))
        assert (N==0)==(coords[0]==coords[1] and coords[2]==coords[3])
        assert 4*N==(2*(coords[0]-coords[1])-(coords[2]-coords[3]))**2+3*(coords[2]-coords[3])**2


def test_actual_product_polynomial_is_Eisenstein_not_Gaussian_multiplication():
    context=tuple('v'+str(i) for i in range(12))
    formula=parse_formula_in_context(candidate.eisenstein_coordinate_product_relation(*context,tag='audit',variables=context),list(context))
    for coords in product(range(3),repeat=8):
        A,B=_represented(coords[:4]),_represented(coords[4:])
        C=_emul(A,B)
        output=_raw(C,padding=3)
        assert _quantifier_free_value(formula,(*coords,*output))
        wrong=(output[0]+1,*output[1:])
        assert not _quantifier_free_value(formula,(*coords,*wrong))
        assert _enorm(C)==_enorm(A)*_enorm(B)
    assert _emul((0,1),(0,1))==(-1,-1)
    assert _emul((0,1),(0,1))!=(-1,0)


def _zcode(value):
    return 2*value if value>=0 else 2*(-value-1)+1


def _zvalue(code):
    return code//2 if code%2==0 else -(code//2+1)


def _paircode(A):
    a,b=(_zcode(value) for value in A)
    return (a+b)*(a+b+1)+2*b


def _pairvalue(code):
    if code<0 or code%2:
        raise ValueError('not a canonical coordinate code')
    diagonal=(isqrt(4*code+1)-1)//2
    second=(code-diagonal*(diagonal+1))//2
    return _zvalue(diagonal-second),_zvalue(second)


def _floor(p,n,M):
    assert M>0
    qp,s=divmod(p+(M-1)*n,M)
    qn=n
    assert p+M*qn==n+M*qp+s
    assert 0<=s<M
    return qp-qn,s


def _divide(A,B):
    M=_enorm(B)
    if M==0:
        raise ValueError('division by zero')
    numerator=_emul(_conj(B),A)
    rp,rn,ip,inn=_raw(numerator,padding=7)
    qr,s=_floor(rp,rn,M)
    qi,t=_floor(ip,inn,M)
    Q=(qr,qi)
    multiple=_emul(B,Q)
    R=(A[0]-multiple[0],A[1]-multiple[1])
    assert _emul(_conj(B),R)==(s,t)
    assert M*_enorm(R)==_enorm((s,t))
    assert _enorm((s,t))<=max(s,t)**2<M*M
    assert _enorm(R)<M
    assert (multiple[0]+R[0],multiple[1]+R[1])==A
    assert _pairvalue(_paircode(Q))==Q
    assert _pairvalue(_paircode(R))==R
    return Q,R,s,t


def test_constructive_floor_division_exhausts_small_signed_inputs_and_nonzero_divisors():
    for a,b,c,d in product(range(-5,6),repeat=4):
        if c==d==0:
            continue
        _divide((a,b),(c,d))


def test_all_six_units_force_zero_remainder_and_zero_dividend_is_allowed():
    units={(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1)}
    assert {(a,b) for a,b in product(range(-2,3),repeat=2) if _enorm((a,b))==1}==units
    for B in units:
        for A in ((0,0),(7,-13),(-19,2),(10**30+7,-10**21-3)):
            _,R,s,t=_divide(A,B)
            assert R==(0,0) and s==t==0
    with pytest.raises(ValueError,match='zero'):
        _divide((1,0),(0,0))


def test_floor_parallelogram_bound_includes_both_upper_corners_and_asymmetric_edges():
    for M in range(1,60):
        for s,t in ((0,0),(M-1,0),(0,M-1),(M-1,M-1)):
            assert _enorm((s,t))<=max(s,t)**2<M*M
            assert _floor(s,0,M)==(0,s)
            assert _floor(t,0,M)==(0,t)
        assert _enorm((M-1,M-1))==(M-1)**2
    # An actual asymmetric upper-edge division, not only a synthetic bound.
    # For M>1 the corner (M-1,M-1) itself cannot be an adjugate error: its norm
    # is 1 modulo M. The stronger parallelogram lemma nevertheless covers it.
    # Divisor 1-ω has norm 3.
    _,_,s,t=_divide((0,-1),(1,-1))
    assert (s,t)==(1,2)


@pytest.mark.parametrize('A,B',(
    ((10**60+7,-10**45+3),(10**25+1,1)),
    ((-10**55-17,10**51+9),(1,-10**22-1)),
    ((0,10**70),(10**31,-10**31+1)),
    ((-10**80,-10**81),(10**19+7,10**23+11)),
))
def test_unbounded_integer_semantics_use_exact_arithmetic_not_float_rounding(A,B):
    _divide(A,B)


def test_canonical_pair_codes_are_shared_injective_and_do_not_accept_odd_noncodes():
    seen=set()
    for A in product(range(-12,13),repeat=2):
        code=_paircode(A)
        assert code not in seen and _pairvalue(code)==A
        assert (code==0)==(A==(0,0))
        seen.add(code)
    for code in range(1,100,2):
        with pytest.raises(ValueError):
            _pairvalue(code)
