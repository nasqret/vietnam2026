"""Bounded fresh-process checks for actual perfect-power root construction."""

from functools import lru_cache
from dataclasses import replace
import gc
from functools import reduce
from math import factorial, gcd, isqrt, prod
import re

import pytest

from peano_lab.library import perfect_power_profile_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library.finite_fold_surface import _beta_at_term
from peano_lab.library.ha_pair_cell_seed_candidate import pair_code
from peano_lab.library.power_algebra_theorems import _power_terms
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from test_prime_valuation_support_candidate import _assert_same_ast, _expected_support, _integer_profile
from test_squarefree_decomposition_candidate import _squarefree_reference, core as parent_core, rows as squarefree_rows


BODY_METRICS = {
    "power_value_eq_transport":(17,11,17),
    "power_one_base_value":(41,18,41),
    "power_one_base_exists":(21,12,21),
    "power_product_construct":(35,23,35),
    "power_divisible_exponent_root":(48,28,48),
    "positive_power_nonzero_base":(27,16,27),
    "positive_power_prime_valuations_divisible":(47,28,47),
    "prime_valuation_divisibility_cofactor":(90,37,90),
    "prime_valuation_divisible_power_root_bounded":(190,44,190),
    "prime_valuation_divisible_power_root_exists":(32,18,32),
    "prime_exponent_common_divisor_drop":(33,22,33),
    "prime_exponent_common_divisor_successor":(44,25,44),
    "prime_exponent_common_divisor_factor":(41,27,41),
    "prime_exponent_prefix_gcd_empty":(22,13,22),
    "prime_exponent_prefix_gcd_successor":(169,53,169),
    "prime_exponent_prefix_gcd_exists":(44,25,44),
    "prime_exponent_prefix_gcd_functional":(49,26,49),
    "prime_valuation_support_nonempty":(76,43,76),
    "prime_valuation_support_exponent_gcd_nonzero":(89,36,88),
    "prime_exponent_entry_has_prime_valuation":(121,34,121),
    "prime_support_common_divisor_implies_all_valuations":(140,40,140),
    "prime_support_all_valuations_implies_common_divisor":(46,31,46),
    "prime_support_exponent_gcd_divisor_criterion":(138,53,138),
    "prime_support_perfect_power_iff_degree_divides":(76,34,76),
    "prime_support_exponent_gcd_roots_available":(35,31,35),
    "perfect_power_root_table_prefix_append":(77,30,77),
    "perfect_power_root_table_conditional_entry":(39,14,39),
    "perfect_power_root_table_prefix_exists":(70,32,70),
    "perfect_power_root_table_exists":(39,23,39),
    "perfect_power_profile_code_exists":(73,38,73),
    "perfect_power_profile_exists":(140,54,139),
    "perfect_power_profile_data_degree_classification":(103,60,103),
    "perfect_power_profile_data_root_lookup":(65,41,65),
    "perfect_power_profile_positive":(94,41,94),
    "perfect_power_profile_unit_code":(85,36,85),
    "perfect_power_profile_nonunit_decode":(19,12,19),
    "positive_squarefree_kernel_and_power_profile":(41,22,41),
}


@lru_cache(maxsize=1)
def core():
    return parent_core() | {r.name:r for r in squarefree_rows()}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_perfect_power_profile_candidate_theorems(TheoremSpec)


@pytest.mark.parametrize("row",rows(),ids=lambda r:r.name)
def test_original_kernel_body(row):
    try:
        receipt = replay_candidate_bodies((row,),core=core() | {r.name:r for r in rows()})[0]
        assert receipt.proof_depth <= 256
        assert receipt.proof_objects <= receipt.proof_nodes
        assert (receipt.proof_nodes,receipt.proof_depth,receipt.proof_objects) == BODY_METRICS[row.name]
        print(f"{row.name}: {receipt.proof_nodes}/{receipt.proof_depth}/{receipt.proof_objects}")
    finally:
        gc.collect()


def test_additive_dependency_order_and_ordinary_commands():
    available = set(core())
    for row in rows():
        assert row.name not in available
        assert set(row.dependencies) <= available
        assert len(set(row.dependencies)) == len(row.dependencies)
        assert all(re.search(r"(?<![\w'])"+re.escape(d)+r"(?![\w'])","\n".join(row.script)) for d in row.dependencies)
        assert not any(c.startswith(("use ","sorry","admit","DNE","ring")) for c in row.script)
        _closed_formula(row.statement)
        available.add(row.name)


FIELDS = ("pb","pc","eb","ec","vb","vc","l","g","rb","rc")


def _both(*parts):
    if len(parts) == 1:
        return parts[0]
    return f"({parts[0]}) /\\ ({_both(*parts[1:])})"


def _at(b,c,i,v,tag):
    return _beta_at_term(b,c,i,v,tag="audit_"+tag,avoid=())


def _pow(a,k,n,tag):
    return _power_terms(a,k,n,tag="audit_"+tag)


def _common_reference(d,tag):
    return f"forall i e. (exists gap. gap + S i = l) -> ({_at('eb','ec','i','e',tag)}) -> exists q. e = ({d}) * q"


def _gcd_reference():
    return _both(_common_reference("g","common"),f"forall d. ({_common_reference('d','greatest')}) -> exists q. g = d * q")


def _root_table_reference(n):
    return f"forall k. ~(k = 0) -> (exists q. g = k * q) -> exists r. ({_at('rb','rc','k','r','root_at')}) /\\ ({_pow('r','k',n,'root_power')})"


def _profile_code_reference(w="w"):
    intermediates = tuple("audit_pair_"+str(i) for i in range(8))
    clauses = [pair_code(w if i==0 else intermediates[i-1],FIELDS[i],intermediates[i]) for i in range(8)]
    clauses.append(pair_code(intermediates[-1],"rb","rc"))
    return "exists " + " ".join(intermediates) + ". (" + _both(*clauses) + ")"


def _data_reference(n="n",w="w"):
    return _both(f"~(({n}) = 1)",_profile_code_reference(w),_expected_support(n),_gcd_reference(),"~(g = 0)",_root_table_reference(n))


def _profile_reference(n="n",w="w"):
    unit = _both(f"({n}) = 1",f"({w}) = 0",f"forall k. ~(k = 0) -> ({_pow('1','k','1','unit_all_degrees')})")
    return f"({unit}) \\/ (exists {' '.join(FIELDS)}. ({_data_reference(n,w)}))"


def test_profile_definition_independently_has_real_pair_data_and_explicit_unit_exception():
    actual = candidate.perfect_power_profile_relation("n","w",tag="public",variables=("n","w"))
    _assert_same_ast(_closed_formula("forall n w. "+actual),_closed_formula("forall n w. "+_profile_reference()))


def test_profile_existence_has_only_positive_input_not_supplied_factors_gcd_or_roots():
    expected = "forall n. ~(n = 0) -> exists w. (" + _profile_reference() + ")"
    row = next(r for r in rows() if r.name == "perfect_power_profile_exists")
    _assert_same_ast(_closed_formula(row.statement),_closed_formula(expected))


def test_full_g010_endpoint_independently_matches_unique_kernel_plus_actual_profile():
    expected = (
        "forall n. ~(n = 0) -> exists r s w. "
        f"({_squarefree_reference('r','kernel')}) /\\ (n = r * (s * s) /\\ "
        f"(({_profile_reference()}) /\\ forall u v. "
        f"({_squarefree_reference('u','comparison')}) -> n = u * (v * v) -> u = r /\\ v = s))"
    )
    row = next(r for r in rows() if r.name == "positive_squarefree_kernel_and_power_profile")
    _assert_same_ast(_closed_formula(row.statement),_closed_formula(expected))


def test_root_lookup_returns_the_actual_decoded_table_entry():
    expected = (
        f"forall n w {' '.join(FIELDS)} k. ({_data_reference()}) -> ~(k = 0) -> "
        f"(exists q. g = k * q) -> exists r. ({_at('rb','rc','k','r','lookup')}) /\\ ({_pow('r','k','n','lookup')})"
    )
    row = next(r for r in rows() if r.name == "perfect_power_profile_data_root_lookup")
    _assert_same_ast(_closed_formula(row.statement),_closed_formula(expected))


def test_encoded_gcd_classification_has_both_directions_and_positive_degree_guard():
    root = f"exists r. ({_pow('r','k','n','classified')})"
    divides = "exists q. g = k * q"
    expected = f"forall n w {' '.join(FIELDS)} k. ({_data_reference()}) -> ~(k = 0) -> (({root}) -> ({divides})) /\\ (({divides}) -> ({root}))"
    row = next(r for r in rows() if r.name == "perfect_power_profile_data_degree_classification")
    _assert_same_ast(_closed_formula(row.statement),_closed_formula(expected))


SURFACES = (
    (candidate.prime_valuations_divisible_relation,("n","k")),
    (candidate.prime_exponent_prefix_gcd_relation,("b","c","l","g")),
    (candidate.perfect_power_root_table_relation,("n","g","b","c")),
    (candidate.perfect_power_profile_code_relation,("w",*FIELDS)),
    (candidate.perfect_power_profile_data_relation,("n","w",*FIELDS)),
    (candidate.perfect_power_profile_relation,("n","w")),
)


@pytest.mark.parametrize("builder,args",SURFACES)
def test_public_surfaces_are_hygienic_alpha_equivalent(builder,args):
    first,names = parse_formula_with_names(builder(*args,tag="first",variables=args))
    second,other = parse_formula_with_names(builder(*args,tag="second",variables=args))
    _assert_same_ast(first,second)
    assert names == other and set(names) == set(args)


@pytest.mark.parametrize("builder,args",SURFACES)
@pytest.mark.parametrize("bad",["", "unknown", "n - 1", "n / 2", "n = 0", "x) -> false", None, 17])
def test_public_surfaces_reject_nonterms_or_undeclared_variables(builder,args,bad):
    with pytest.raises((ValueError,TypeError)):
        builder(bad,*args[1:],tag="audit",variables=args)


@pytest.mark.parametrize("builder,args",SURFACES)
@pytest.mark.parametrize("context",[(),("n","n"),["n"],("forall",)])
def test_public_surfaces_require_valid_explicit_context(builder,args,context):
    with pytest.raises((ValueError,TypeError)):
        builder(*args,tag="audit",variables=context)


@pytest.mark.parametrize("builder,args",SURFACES)
@pytest.mark.parametrize("tag",["", "S", "forall", "bad tag", "x) -> false", None, 17])
def test_public_surfaces_reject_bad_tags(builder,args,tag):
    with pytest.raises((ValueError,TypeError)):
        builder(*args,tag=tag,variables=args)


@pytest.mark.parametrize("value",["n + 1","n * n","123456789012345678901234567890"])
def test_profile_preserves_compound_and_double_and_add_terms(value):
    actual = candidate.perfect_power_profile_relation(value,"w",tag="compound",variables=("n","w"))
    _assert_same_ast(_closed_formula("forall n w. "+actual),_closed_formula("forall n w. "+_profile_reference(value)))


@pytest.mark.parametrize("variable",["ppf_pb_capture","ppf_unit_degree_captureunit"])
def test_profile_rejects_generated_binder_capture(variable):
    with pytest.raises(ValueError,match="capture"):
        candidate.perfect_power_profile_relation(variable,"w",tag="capture",variables=(variable,"w"))


@pytest.mark.parametrize("name",[
    "prime_valuation_divisible_power_root_exists","prime_support_perfect_power_iff_degree_divides",
    "perfect_power_profile_exists","positive_squarefree_kernel_and_power_profile",
])
def test_poisoned_perfect_power_endpoints_are_rejected(name):
    row = next(r for r in rows() if r.name == name)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement="0 = 1"),),core=core()|{r.name:r for r in rows()})


def _pair_value(a,b):
    return (a+b)*(a+b+1)+2*b


def _unpair_value(z):
    if z < 0 or z%2:
        raise ValueError("not a doubled-Cantor Pair code")
    total = (isqrt(4*z+1)-1)//2
    remainder = z-total*(total+1)
    if remainder%2 or remainder//2 > total:
        raise ValueError("outside the actual Pair shell")
    b = remainder//2
    a = total-b
    assert _pair_value(a,b) == z
    return a,b


def _encode_fields(values):
    assert len(values) == 10
    code = _pair_value(*values[-2:])
    for value in reversed(values[:-2]):
        code = _pair_value(value,code)
    return code


def _decode_fields(code):
    values = []
    for _ in range(8):
        value,code = _unpair_value(code)
        values.append(value)
    return (*values,*_unpair_value(code))


def _beta_code(values):
    if not values:
        return 0,0
    scale = (max(values)+1)*factorial(len(values))
    moduli = [1+(i+1)*scale for i in range(len(values))]
    modulus = prod(moduli)
    code = sum(a*(modulus//m)*pow(modulus//m,-1,m) for a,m in zip(values,moduli))%modulus
    assert [code%(1+(i+1)*scale) for i in range(len(values))] == list(values)
    return code,scale


def _model_profile(n):
    factors = _integer_profile(n)
    if n == 1:
        return 0,None,()
    exponent_gcd = reduce(gcd,(e for p,e,v in factors),0)
    assert exponent_gcd > 0
    roots = [0]+[prod(p**(e//k) for p,e,v in factors) if exponent_gcd%k==0 else 0 for k in range(1,exponent_gcd+1)]
    values = (*_beta_code([p for p,e,v in factors]),*_beta_code([e for p,e,v in factors]),
              *_beta_code([v for p,e,v in factors]),len(factors),exponent_gcd,*_beta_code(roots))
    return _encode_fields(values),exponent_gcd,tuple(roots)


def _integer_root_floor(n,k):
    if n < 1 or k < 1:
        raise ValueError("positive input and degree required")
    low,high = 0,n+1
    while high-low > 1:
        mid = (high+low)//2
        if mid**k <= n:
            low = mid
        else:
            high = mid
    return low


@pytest.mark.parametrize("n",[2,4,8,12,36,64,72,144,729,900,4096,2**12*3**6])
def test_actual_pair_and_beta_models_decode_complete_support_gcd_and_roots(n):
    # Independent arithmetic models validate the promised data format. They
    # are explicitly not a replacement for the ordinary-kernel certificates.
    code,exponent_gcd,roots = _model_profile(n)
    pb,pc,eb,ec,vb,vc,l,g,rb,rc = _decode_fields(code)
    primes = [pb%(1+(i+1)*pc) for i in range(l)]
    exponents = [eb%(1+(i+1)*ec) for i in range(l)]
    powers = [vb%(1+(i+1)*vc) for i in range(l)]
    assert len(primes)==len(set(primes)) and all(e>0 for e in exponents)
    assert list(zip(primes,exponents,powers)) == _integer_profile(n)
    assert prod(powers)==n and g==exponent_gcd==reduce(gcd,exponents)
    assert tuple(rb%(1+(k+1)*rc) for k in range(g+1)) == roots
    for k in range(1,g+4):
        root = _integer_root_floor(n,k)
        assert (root**k==n) == (g%k==0)
        if g%k==0:
            assert roots[k]**k==n and roots[k]==root


@pytest.mark.parametrize("n",range(2,102))
def test_independent_small_models_classify_all_tested_positive_degrees(n):
    exponent_gcd = reduce(gcd,(e for p,e,v in _integer_profile(n)),0)
    for k in range(1,13):
        root = _integer_root_floor(n,k)
        assert (root**k==n) == (exponent_gcd%k==0)


@pytest.mark.parametrize("degree",[1,2,3,17,97,10000,10**20])
def test_unit_profile_uses_uniform_identity_not_a_finite_positive_exponent_gcd(degree):
    assert _model_profile(1) == (0,None,())
    assert 1**degree == 1


def test_zero_input_and_zero_perfect_power_degree_are_not_accepted():
    with pytest.raises(ValueError):
        _model_profile(0)
    with pytest.raises(ValueError):
        _integer_root_floor(8,0)
    with pytest.raises(ValueError):
        _unpair_value(1)
