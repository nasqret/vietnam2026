"""Unsealed Gaussian authoring checks; not a dependency-closure admission receipt."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
import json
from math import isqrt
from pathlib import Path
import re

import pytest

from peano_lab.kernel.formulas import And, Bot, Eq, Exists, Forall, Imp, parse_formula_in_context, parse_formula_with_names
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero
from peano_lab.library import gaussian_euclidean_candidate as candidate
from peano_lab.library.gaussian_euclidean_candidate import make_gaussian_euclidean_candidate_theorems
from peano_lab.library.ha_signed_balance_candidate import signed_balance
from peano_lab.library.ha_signed_decode_candidate import signed_decode
from peano_lab.library.signed_integer_division_candidate import make_signed_integer_division_candidate_theorems
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula


ROOT = Path(__file__).resolve().parents[3]
PARENT = ROOT / "artifacts/peano-library/alpha/catalog-v27.json"
PARENT_SHA256 = "481a9a378e54dc389422819587e8377a07b63a0d5d50286ffdfd28f0c4bdb2e6"
EXPECTED_NAMES = (
    'gaussian_signed_square_exists','gaussian_signed_square_functional',
    'gaussian_signed_square_negated','gaussian_signed_square_integer_transport',
    'gaussian_signed_product_square_positive','gaussian_signed_product_square_negative',
    'gaussian_signed_product_square_compensation','gaussian_signed_square_product',
    'gaussian_signed_sum_square_positive','gaussian_signed_sum_square_negative',
    'gaussian_signed_square_sum_compensation','gaussian_signed_square_difference_compensation',
    'gaussian_signed_norm_exists','gaussian_signed_norm_functional',
    'gaussian_signed_product_interchange_positive','gaussian_signed_product_interchange_negative',
    'gaussian_signed_product_commutative','gaussian_signed_product_shuffle',
    'gaussian_signed_product_cross_interchange','gaussian_signed_square_lagrange',
    'gaussian_signed_norm_product','gaussian_signed_norm_integer_transport',
    'gaussian_signed_norm_conjugate','gaussian_signed_square_zero_iff',
    'gaussian_signed_norm_nonzero','gaussian_signed_square_scaled',
    'gaussian_product_associate_real_positive','gaussian_product_associate_real_negative',
    'gaussian_product_associate_imaginary_positive','gaussian_product_associate_imaginary_negative',
    'gaussian_product_difference_real_positive','gaussian_product_difference_real_negative',
    'gaussian_product_difference_imaginary_positive','gaussian_product_difference_imaginary_negative',
    'gaussian_product_associate','gaussian_product_difference','gaussian_equal_reflexive',
    'gaussian_equal_symmetric','gaussian_equal_transitive','gaussian_product_integer_congruence',
    'gaussian_difference_integer_congruence','gaussian_signed_norm_balance',
    'gaussian_conjugate_product_is_norm','gaussian_natural_scalar_product',
    'gaussian_adjoint_product_is_norm_scale','gaussian_residual_conjugate_identity',
    'gaussian_difference_reconstructs_dividend','gaussian_nonzero_natural_positive',
    'gaussian_double_square_strict','gaussian_half_double_square_strict',
    'gaussian_two_half_squares_strict','gaussian_nearest_signed_quotient_exists',
    'gaussian_signed_euclidean_division_exists','gaussian_signed_balance_integer_transport',
    'gaussian_signed_balance_same_code','gaussian_decode_from_signed_codes',
    'gaussian_decode_functional','gaussian_representation_exists',
    'gaussian_representation_functional','gaussian_representation_integer_transport',
    'gaussian_representation_equal','gaussian_representation_decode',
    'gaussian_decode_representation','gaussian_representation_is_gaussian',
    'gaussian_pair_zero_codes','gaussian_representation_zero_iff','gaussian_decode_zero_iff',
    'gaussian_signed_add_of_balances','gaussian_signed_add_to_balance',
    'gaussian_signed_mul_of_balances','gaussian_signed_mul_to_balance',
    'gaussian_norm_of_representation','gaussian_norm_for_representation',
    'gaussian_norm_exists','gaussian_norm_functional','gaussian_norm_exists_unique',
    'gaussian_sum_integer_congruence','gaussian_add_of_representations',
    'gaussian_add_for_representations','gaussian_add_exists','gaussian_add_functional',
    'gaussian_multiply_of_representations','gaussian_multiply_for_representations',
    'gaussian_multiply_exists','gaussian_multiply_functional','gaussian_norm_multiply',
    'gaussian_division_remainder_of_representations','gaussian_euclidean_division_exists',
)
EXPECTED_BODY_METRICS = dict(zip(EXPECTED_NAMES,(
    (30,18),(25,17),(16,11),(106,32),(614,40),(615,40),(86,32),(37,22),
    (351,73),(335,71),(611,84),(61,36),(21,13),(73,39),
    (227,56),(227,56),(44,15),(88,23),(91,24),(83,44),(245,58),
    (95,43),(48,29),(94,26),(57,22),(123,27),
    (736,63),(736,63),(736,63),(736,63),(387,83),(387,83),(387,83),(387,83),
    (73,32),(73,32),(7,6),(22,16),(90,39),(274,75),(147,56),(157,47),
    (266,37),(106,23),(108,39),(242,97),(118,26),
    (22,11),(37,16),(80,26),(128,38),(166,34),(242,70),
    (39,24),(72,28),(16,14),(196,34),(21,13),(107,27),(95,43),
    (106,31),(74,39),(62,29),(28,17),
    (65,30),(207,37),(53,31),(79,34),(66,29),(79,34),(66,29),
    (15,14),(107,59),(38,20),(80,43),(22,15),(110,47),
    (27,25),(238,108),(62,32),(119,63),(27,25),(238,108),(62,32),(119,63),
    (172,77),(97,48),(199,65),
),strict=True))
ROOT_PINS = {
    'gaussian_signed_euclidean_division_exists':'b74e03b044aac9c837f2098ad4e3d75a977fddf0d331ae84e02d440d422c91d8',
    'gaussian_representation_zero_iff':'7fa8a228116bfb6de5d50cd5782c6e33cc4e659ff2a2c4725d0979e77f0d6a08',
    'gaussian_norm_exists_unique':'452d832311908cb4fca7139b9147039b0a05331967073d0b1743117f510599fd',
    'gaussian_add_exists':'af126fdb2cc45f1f1b2620570ac6e6759b4e3118a25acaa96862b53971ec255d',
    'gaussian_multiply_exists':'3ded8b89b9624cb91cd7a7eb23ea6a2921aa912aba4dc6a8c35d8d308d3971d0',
    'gaussian_norm_multiply':'b9f32039576506c3cabe3efcb762725f554089562b866d504fb0f92187159c64',
    'gaussian_euclidean_division_exists':'7c20ce64493b15888f961ece2d86e97171370aee53e8517ee21db8d53d82fd10',
}


@lru_cache(maxsize=1)
def rows():
    return make_gaussian_euclidean_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    raw = PARENT.read_bytes()
    assert sha256(raw).hexdigest() == PARENT_SHA256
    source = json.loads(raw)
    assert source["schema"] == "peano-library-alpha-snapshot-v27"
    assert source["theorem_count"] == source["checked_use_count"] == 2560
    assert source["stable_count"] == 432
    table = {
        item["name"]: TheoremSpec(item["name"],item["statement"],tuple(item["dependencies"]),tuple(item["script"]),item["summary"])
        for item in source["theorems"]
    }
    return table | {row.name:row for row in make_signed_integer_division_candidate_theorems(TheoremSpec)}


@pytest.mark.parametrize("name",EXPECTED_NAMES)
def test_gaussian_body_passes_original_kernel(name):
    table = {row.name:row for row in rows()}
    try:
        receipt = replay_candidate_bodies((table[name],),core=core()|table)[0]
        assert receipt.name == name
        assert (receipt.proof_nodes,receipt.proof_depth) == EXPECTED_BODY_METRICS[name]
        assert receipt.proof_depth <= 256 and receipt.proof_objects <= receipt.proof_nodes
        assert receipt.proof_edges == receipt.proof_nodes-1
    finally:
        gc.collect()


def test_inventory_is_exact_fresh_acyclic_and_constructive():
    assert tuple(row.name for row in rows()) == EXPECTED_NAMES
    assert len(rows()) == 88
    assert sum(len(row.dependencies) for row in rows()) == 303
    assert sum(len(row.script) for row in rows()) == 4462
    assert sha256('\n'.join(EXPECTED_NAMES).encode()).hexdigest() == '1d25a21b70918e4de3586fb7a12ad23ab66cf1b14779a6d11097171c1c10b9a8'
    available=set(core())
    for row in rows():
        assert row.name not in available
        assert len(row.dependencies) == len(set(row.dependencies))
        assert set(row.dependencies) <= available
        assert all(re.search(r"(?<![\w'])"+re.escape(dep)+r"(?![\w'])",'\n'.join(row.script)) for dep in row.dependencies)
        assert not any(command.startswith(('use ','ring','admit','sorry','DNE')) for command in row.script)
        assert not any('eisenstein' in dep for dep in row.dependencies)
        _closed_formula(row.statement)
        available.add(row.name)


@pytest.mark.parametrize('name',EXPECTED_NAMES)
def test_forged_conclusion_is_rejected_by_original_kernel(name):
    table={row.name:row for row in rows()}
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(table[name],statement=f'({table[name].statement}) /\\ false'),),core=core()|table)
    gc.collect()


@pytest.mark.parametrize('name',ROOT_PINS)
def test_principal_statement_bytes_are_independently_pinned(name):
    row=next(row for row in rows() if row.name==name)
    assert sha256(row.statement.encode()).hexdigest() == ROOT_PINS[name]


@pytest.mark.parametrize('name',ROOT_PINS)
def test_missing_principal_dependency_is_rejected(name):
    table={row.name:row for row in rows()}
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(table[name],dependencies=table[name].dependencies[1:]),),core=core()|table)
    gc.collect()


def _both(*parts):
    result=f'({parts[-1]})'
    for part in reversed(parts[:-1]):
        result=f'({part}) /\\ ({result})'
    return result


def _reference_sd(code,p,n,tag):
    k='test_half_'+tag
    return f'(({code})=2*({p}) /\\ ({n})=0) \\/ exists {k}. ((({code})=2*{k}+1 /\\ ({p})=0) /\\ ({n})=S {k})'


def _reference_balance(code,p,n,tag):
    u,v='test_p_'+tag,'test_n_'+tag
    return f'exists {u} {v}. '+_both(_reference_sd(code,u,v,tag+'decode'),f'({p})+{v}=({n})+{u}')


def _reference_pair(code,A,tag,*,normalized=False):
    rc,ic='test_real_'+tag,'test_imag_'+tag
    graph=_reference_sd if normalized else _reference_balance
    return f'exists {rc} {ic}. '+_both(f'({code})=({rc}+{ic})*S({rc}+{ic})+({ic}+{ic})',graph(rc,*A[:2],tag+'real'),graph(ic,*A[2:],tag+'imaginary'))


def _reference_valid(code,tag):
    A=tuple('test_valid_'+label+'_'+tag for label in ('rp','rn','ip','in'))
    return f'exists {" ".join(A)}. ({_reference_pair(code,A,tag+"decode",normalized=True)})'


def _reference_square(p,n,N):
    return f'({p})*({p})+({n})*({n})=({N})+(({p})*({n})+({n})*({p}))'


def _reference_raw_norm(A,N,tag):
    u,v='test_real_square_'+tag,'test_imaginary_square_'+tag
    return f'exists {u} {v}. '+_both(_reference_square(*A[:2],u),_reference_square(*A[2:],v),f'({N})={u}+{v}')


def _reference_norm(code,N,tag):
    A=tuple('test_norm_'+label+'_'+tag for label in ('rp','rn','ip','in'))
    return f'exists {" ".join(A)}. '+_both(_reference_pair(code,A,tag+'representation'),_reference_raw_norm(A,N,tag+'raw'))


def _reference_product(A,B):
    a,b,c,d=A
    e,f,g,h=B
    return (f'(({a})*({e})+({b})*({f}))+(({c})*({h})+({d})*({g}))',
            f'(({a})*({f})+({b})*({e}))+(({c})*({g})+({d})*({h}))',
            f'(({a})*({g})+({b})*({h}))+(({c})*({e})+({d})*({f}))',
            f'(({a})*({h})+({b})*({g}))+(({c})*({f})+({d})*({e}))')


def _reference_operation(a,b,c,tag,*,multiply):
    A=tuple('test_first_'+label+'_'+tag for label in ('rp','rn','ip','in'))
    B=tuple('test_second_'+label+'_'+tag for label in ('rp','rn','ip','in'))
    C=_reference_product(A,B) if multiply else tuple(f'({x})+({y})' for x,y in zip(A,B,strict=True))
    return f'exists {" ".join((*A,*B))}. '+_both(_reference_pair(a,A,tag+'first'),_reference_pair(b,B,tag+'second'),_reference_pair(c,C,tag+'result'))


def _reference_divrem(a,b,q,r,tag):
    product='test_product_'+tag
    return f'exists {product}. '+_both(_reference_operation(b,q,product,tag+'multiply',multiply=True),_reference_operation(product,r,a,tag+'add',multiply=False))


def _reference_euclidean(a,b,q,r,U,V,tag):
    return _both(_reference_valid(q,tag+'quotient'),_reference_valid(r,tag+'remainder'),_reference_divrem(a,b,q,r,tag+'equation'),_reference_norm(r,U,tag+'smallnorm'),_reference_norm(b,V,tag+'largenorm'),f'exists test_gap_{tag}. test_gap_{tag}+S({U})=({V})')


def _same_formula(actual,expected,variables):
    assert parse_formula_in_context(actual,list(variables)) == parse_formula_in_context(expected,list(variables))


def test_shared_carrier_is_exactly_the_historic_signed_decoder_and_balance():
    _same_formula(candidate._sd('code','p','n','first'),signed_decode('code','p','n',tag='historic'),('code','p','n'))
    _same_formula(candidate._balance('code','p','n','first'),signed_balance('code','p','n',tag='historic'),('code','p','n'))
    args=('z','a','b','c','d')
    _same_formula(candidate.gaussian_decode_relation(*args,tag='code'),_reference_pair('z',args[1:],'audit',normalized=True),args)
    _same_formula(candidate.gaussian_representation_relation(*args,tag='rep'),_reference_pair('z',args[1:],'audit'),args)
    _same_formula(candidate.gaussian_integer_relation('z',tag='valid'),_reference_valid('z','audit'),('z',))


def test_actual_gaussian_norm_add_product_and_division_definitions_are_independent_polynomial_graphs():
    _same_formula(candidate.gaussian_norm_relation('z','N',tag='norm'),_reference_norm('z','N','audit'),('z','N'))
    _same_formula(candidate.gaussian_add_relation('a','b','c',tag='add'),_reference_operation('a','b','c','audit',multiply=False),('a','b','c'))
    _same_formula(candidate.gaussian_multiply_relation('a','b','c',tag='mul'),_reference_operation('a','b','c','audit',multiply=True),('a','b','c'))
    _same_formula(candidate.gaussian_division_remainder_relation('a','b','q','r',tag='division'),_reference_divrem('a','b','q','r','audit'),('a','b','q','r'))
    args=('a','b','q','r','U','V')
    _same_formula(candidate.gaussian_euclidean_division_relation(*args,tag='euclidean'),_reference_euclidean(*args,'audit'),args)


def test_full_canonical_root_has_only_carrier_and_nonzero_divisor_premises():
    expected=f"forall a b. ({_reference_valid('a','first')}) -> ({_reference_valid('b','second')}) -> ~(b = 0) -> exists q r U V. ({_reference_euclidean('a','b','q','r','U','V','answer')})"
    actual=next(row.statement for row in rows() if row.name=='gaussian_euclidean_division_exists')
    assert _closed_formula(actual) == _closed_formula(expected)
    formula=_closed_formula(actual)
    assert type(formula) is Forall and type(formula.body) is Forall
    body=formula.body.body
    assert type(body) is Imp and type(body.left) is Exists
    assert type(body.right) is Imp and type(body.right.left) is Exists
    assert body.right.right.left == Imp(Eq(Var(0),Zero()),Bot())
    result=body.right.right.right
    for _ in range(4):
        assert type(result) is Exists
        result=result.body
    assert type(result) is And


def test_full_raw_root_has_only_the_actual_nonzero_signed_divisor_premise():
    A,B,Q,R=('a','b','c','d'),('e','f','g','h'),('qp','qn','ip','in'),('rp','rn','sp','sn')
    product=_reference_product(B,Q)
    total=tuple(f'({x})+({y})' for x,y in zip(product,R,strict=True))
    equations=_both(f'({total[0]})+({A[1]})=({A[0]})+({total[1]})',f'({total[2]})+({A[3]})=({A[2]})+({total[3]})')
    output=_both(equations,_reference_raw_norm(R,'U','remainder'),_reference_raw_norm(B,'V','divisor'),'exists gap. gap+S U=V')
    expected=f"forall {' '.join((*A,*B))}. ~(e=f /\\ g=h) -> exists {' '.join((*Q,*R,'U','V'))}. ({output})"
    actual=next(row.statement for row in rows() if row.name=='gaussian_signed_euclidean_division_exists')
    assert _closed_formula(actual) == _closed_formula(expected)


@pytest.mark.parametrize('name,guard',(
    ('gaussian_euclidean_division_exists','~(bc = 0) -> '),
    ('gaussian_signed_euclidean_division_exists','~(e = f /\\ g = h) -> '),
))
def test_zero_divisor_guard_cannot_be_removed_from_the_checked_proof(name,guard):
    table={row.name:row for row in rows()}
    changed=replace(table[name],statement=table[name].statement.replace(guard,'',1))
    assert changed.statement != table[name].statement
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,),core=core()|table)
    gc.collect()


SURFACES=(
    (candidate.gaussian_signed_norm_relation,('a','b','c','d','N')),
    (candidate.gaussian_decode_relation,('z','a','b','c','d')),
    (candidate.gaussian_representation_relation,('z','a','b','c','d')),
    (candidate.gaussian_integer_relation,('z',)),
    (candidate.gaussian_rounded_signed_division_relation,('p','n','N','qp','qn','ep','en','t')),
    (candidate.gaussian_signed_division_remainder_relation,tuple('v'+str(index) for index in range(18))),
    (candidate.gaussian_norm_relation,('z','N')),
    (candidate.gaussian_add_relation,('a','b','c')),
    (candidate.gaussian_multiply_relation,('a','b','c')),
    (candidate.gaussian_division_remainder_relation,('a','b','q','r')),
    (candidate.gaussian_euclidean_division_relation,('a','b','q','r','U','V')),
)


@pytest.mark.parametrize('builder,arguments',SURFACES)
def test_conservative_surface_free_variables_and_alpha_renaming(builder,arguments):
    first,names=parse_formula_with_names(builder(*arguments,tag='first'))
    second,other_names=parse_formula_with_names(builder(*arguments,tag='second'))
    assert first == second and names == other_names
    assert set(names) == set(arguments)


@pytest.mark.parametrize('builder,arguments',SURFACES)
@pytest.mark.parametrize('bad',('','S','forall','false','x) -> false','a+b','ge_capture','sd_capture','sb_capture','sif_capture',None,17))
def test_definition_argument_rejection_prevents_injection_and_inherited_capture(builder,arguments,bad):
    with pytest.raises(ValueError):
        builder(bad,*arguments[1:],tag='audit')


@pytest.mark.parametrize('builder,arguments',SURFACES)
@pytest.mark.parametrize('bad',('','S','forall','bad tag','x) -> false',None,17))
def test_definition_tags_are_validated(builder,arguments,bad):
    with pytest.raises(ValueError):
        builder(*arguments,tag=bad)


@pytest.mark.parametrize('builder,arguments',tuple(item for item in SURFACES if len(item[1])>1))
def test_surface_parameters_cannot_alias_generated_contexts(builder,arguments):
    with pytest.raises(ValueError):
        builder(arguments[1],*arguments[1:],tag='audit')


def test_square_surface_is_the_actual_subtraction_free_square():
    _same_formula(candidate.signed_difference_square_relation('p','n','s'),'p*p+n*n=s+(p*n+n*p)',('p','n','s'))
    for bad in ('','S','forall','p+n','ge_capture','sd_capture',None):
        with pytest.raises(ValueError):
            candidate.signed_difference_square_relation(bad,'n','s')


def _zcode(value):
    return 2*value if value>=0 else 2*(-value-1)+1


def _zvalue(code):
    return code//2 if code%2==0 else -(code//2+1)


def _gcode(value):
    a,b=(_zcode(part) for part in value)
    return (a+b)*(a+b+1)+2*b


def _gvalue(code):
    if code<0 or code%2:
        raise ValueError('not a canonical natural coordinate pair code')
    diagonal=(isqrt(4*code+1)-1)//2
    imaginary=(code-diagonal*(diagonal+1))//2
    real=diagonal-imaginary
    assert 0<=imaginary<=diagonal
    return _zvalue(real),_zvalue(imaginary)


def _nearest(p,n,N):
    assert N>0
    qp,residue=divmod(p+(N-1)*n,N)
    qn=n
    assert p+N*qn == n+N*qp+residue
    if 2*residue>N:
        qp+=1
        ep,en=0,N-residue
    else:
        ep,en=residue,0
    assert p+N*qn+en == n+N*qp+ep
    assert 2*abs(ep-en)<=N
    return qp-qn,ep-en


def _gmul(A,B):
    return A[0]*B[0]-A[1]*B[1],A[0]*B[1]+A[1]*B[0]


def test_canonical_codes_cover_all_quadrants_zero_and_units_without_accepting_odd_noncodes():
    seen={}
    for a in range(-20,21):
        for b in range(-20,21):
            value=(a,b)
            code=_gcode(value)
            assert code not in seen
            seen[code]=value
            assert _gvalue(code)==value
            assert (code==0)==(value==(0,0))
    for code in range(1,500,2):
        with pytest.raises(ValueError):
            _gvalue(code)
    for unit in ((1,0),(-1,0),(0,1),(0,-1)):
        assert sum(part*part for part in _gvalue(_gcode(unit)))==1


def test_nearest_quotient_algorithm_handles_overlapping_pairs_signs_and_half_ties():
    for p in range(12):
        for n in range(12):
            for N in range(1,20):
                q,e=_nearest(p,n,N)
                assert p-n==N*q+e
                assert 2*abs(e)<=N
                assert p*p+n*n==(p-n)**2+p*n+n*p


def test_actual_gaussian_division_algorithm_exhausts_small_dividends_and_nonzero_divisors():
    for a in range(-5,6):
        for b in range(-5,6):
            for c in range(-5,6):
                for d in range(-5,6):
                    if c==d==0:
                        continue
                    N=c*c+d*d
                    real,imaginary=c*a+d*b,c*b-d*a
                    qr,er=_nearest(max(real,0)+3,max(-real,0)+3,N)
                    qi,ei=_nearest(max(imaginary,0)+2,max(-imaginary,0)+2,N)
                    product=_gmul((c,d),(qr,qi))
                    remainder=(a-product[0],b-product[1])
                    U=sum(part*part for part in remainder)
                    assert N*U==er*er+ei*ei
                    assert U<N
                    assert _gvalue(_gcode((qr,qi)))==(qr,qi)
                    assert _gvalue(_gcode(remainder))==remainder
                    assert (a,b)==(product[0]+remainder[0],product[1]+remainder[1])
                    if N==1:
                        assert remainder==(0,0)


def test_two_half_bounds_really_imply_strict_square_norm_decrease_including_N_one():
    for N in range(1,50):
        for a in range(N//2+1):
            for b in range(N//2+1):
                assert a*a+b*b<N*N
    assert not 0<0  # no Euclidean remainder can satisfy the zero-divisor norm bound


@pytest.mark.parametrize('left,right',(
    ('(2*a+3*b)*(c+d)','2*(a*c+a*d)+3*(b*c+b*d)'),
    ('(a*b)*(c*d)','(d*b)*(a*c)'),
    ('0*a+b*1','b'),
))
def test_bounded_polynomial_guide_still_requires_original_kernel_equality_certificates(left,right):
    row=TheoremSpec('gaussian_polynomial_guide_regression',f'forall a b c d. {left} = {right}',candidate._polynomial_expansion_dependencies(left,right),('intro a','intro b','intro c','intro d')+candidate._commutative_expansion_identity(left,right),'Untrusted guide regression; every equality step is still checked.')
    receipt=replay_candidate_bodies((row,),core=core())[0]
    assert receipt.proof_depth<=256
    gc.collect()


@pytest.mark.parametrize('left,right',(
    ('a*b','a+b'),
    ('2*a','3*a'),
    ('a*b*c*d*e*f*g*h*i','i*h*g*f*e*d*c*b*a'),
    ('65*a','a*65'),
))
def test_polynomial_authoring_guide_rejects_false_or_over_budget_requests(left,right):
    with pytest.raises(ValueError):
        candidate._commutative_expansion_identity(left,right)
