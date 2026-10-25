"""Actual finite Gaussian products and norm-descending prime factorization.

The beta-coded product trace starts at Gaussian one, whose canonical code
is six.  Its steps use the actual frozen Gaussian multiplication graph.
No factor list contains a factorization or uniqueness conclusion as data.
This additive authoring source alone grants no Alpha admission authority.
"""

from __future__ import annotations

from typing import Any,Callable

from . import gaussian_ring_candidate as gr
from . import gaussian_euclidean_candidate as ge
from . import gaussian_factor_search_candidate as search
from . import prime_factorization_permutation_candidate as permutation
from .finite_fold_surface import _beta_at_term


_and=gr._and
_call=gr._call
_intro=gr._intro
_exists=gr._exists
_cases=gr._cases
_parts=gr._parts
_part=gr._part
_valid=gr._valid
_norm=gr._norm
_mul=gr._mul
_unit=gr._unit
_dvd=gr._dvd
_irreducible=gr._irreducible
_prime=gr._prime
_lt=ge._lt
_le=ge._le
_preserve=permutation._preserve


def _at(b: str,c: str,i: str,a: str,tag: str) -> str:
    return _beta_at_term(b,c,i,a,tag='gprod_'+tag,avoid=())


def _steps(b: str,c: str,h: str,e: str,l: str,tag: str) -> str:
    i,a,P,Q=gr._names(tag,'product_index','product_factor','product_before','product_after')
    return f"forall {i}. ({_lt(i,l,tag+'index_bound')}) -> exists {a} {P} {Q}. "+_and(
        _at(b,c,i,a,tag+'factor'),_at(h,e,i,P,tag+'before'),_at(h,e,f'S ({i})',Q,tag+'after'),_mul(P,a,Q,tag+'multiply'))


def _product(b: str,c: str,l: str,P: str,tag: str) -> str:
    h,e=gr._names(tag,'product_trace','product_scale')
    return f"exists {h} {e}. "+_and(_at(h,e,'0','6',tag+'start'),_at(h,e,l,P,tag+'end'),_steps(b,c,h,e,l,tag+'steps'))


def _all_irreducible(b: str,c: str,l: str,tag: str) -> str:
    i,p=gr._names(tag,'factor_index','factor_value')
    return f"forall {i} {p}. ({_lt(i,l,tag+'index')}) -> ({_at(b,c,i,p,tag+'entry')}) -> ({_irreducible(p,tag+'irreducible')})"


def _all_prime(b: str,c: str,l: str,tag: str) -> str:
    i,p=gr._names(tag,'prime_factor_index','prime_factor_value')
    return f"forall {i} {p}. ({_lt(i,l,tag+'index')}) -> ({_at(b,c,i,p,tag+'entry')}) -> ({_prime(p,tag+'prime')})"


def _factor(z: str,unit: str,b: str,c: str,l: str,tag: str) -> str:
    P,=gr._names(tag,'factor_product')
    return _and(_unit(unit,tag+'unit'),_all_irreducible(b,c,l,tag+'irreducible'),
                f"exists {P}. "+_and(_product(b,c,l,P,tag+'trace'),_mul(unit,P,z,tag+'reconstruct')))


def _prime_factor(z: str,unit: str,b: str,c: str,l: str,tag: str) -> str:
    P,=gr._names(tag,'prime_factor_product')
    return _and(_unit(unit,tag+'unit'),_all_prime(b,c,l,tag+'primes'),
                f"exists {P}. "+_and(_product(b,c,l,P,tag+'trace'),_mul(unit,P,z,tag+'reconstruct')))


def gaussian_product_relation(b: str,c: str,l: str,P: str,*,tag: str,variables: tuple[str,...]) -> str:
    """Actual beta-coded repeated Gaussian multiplication starting at code six."""
    return gr._definition(_product,(b,c,l,P),tag=tag,variables=variables)


def gaussian_all_irreducible_relation(b: str,c: str,l: str,*,tag: str,variables: tuple[str,...]) -> str:
    return gr._definition(_all_irreducible,(b,c,l),tag=tag,variables=variables)


def gaussian_all_prime_relation(b: str,c: str,l: str,*,tag: str,variables: tuple[str,...]) -> str:
    return gr._definition(_all_prime,(b,c,l),tag=tag,variables=variables)


def gaussian_irreducible_factorization_relation(z: str,unit: str,b: str,c: str,l: str,*,tag: str,variables: tuple[str,...]) -> str:
    """An actual unit times an actual finite product of irreducible Gaussian factors."""
    return gr._definition(_factor,(z,unit,b,c,l),tag=tag,variables=variables)


def gaussian_prime_factorization_relation(z: str,unit: str,b: str,c: str,l: str,*,tag: str,variables: tuple[str,...]) -> str:
    """An actual unit times an actual finite product of RingPrime Gaussian factors."""
    return gr._definition(_prime_factor,(z,unit,b,c,l),tag=tag,variables=variables)


def _basic_product_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'gaussian_product_beta_index_transport',f"forall b c i j a. i=j -> ({_at('b','c','i','a','index_transport_source')}) -> ({_at('b','c','j','a','index_transport_target')})",
            (),_intro('b','c','i','j','a','heq','h')+('rewrite heq at h',)*2+('exact h',),
            'Equality of beta indices transports the actual bounded remainder entry in both occurrences of its modulus.',
        ),
        spec(
            'gaussian_product_beta_value_transport',f"forall b c i a d. a=d -> ({_at('b','c','i','a','value_transport_source')}) -> ({_at('b','c','i','d','value_transport_target')})",
            (),_intro('b','c','i','a','d','heq','h')+('rewrite heq at h',)*2+('exact h',),
            'Equality of factor codes transports both boundedness and the actual beta remainder equation.',
        ),
        spec(
            'gaussian_product_empty_exists',f"forall b c. ({_product('b','c','0','6','empty_product')})",
            ('gaussian_search_no_index_below_zero',),
            _intro('b','c')+_exists('6','6')+('split','split','exists 0','norm_num','exists 0','norm_num','split','split','exists 0','norm_num','exists 0','norm_num')
            +_intro('i','hi')+('exfalso',)+_call('gaussian_search_no_index_below_zero','i')+('exact hi',),
            'Every empty Gaussian factor prefix has a genuine constant product trace with canonical value six, not natural one.',
        ),
        spec(
            'gaussian_product_empty_value',f"forall b c P. ({_product('b','c','0','P','empty_product_value')}) -> P=6",
            ('beta_at_unique',),_intro('b','c','P','hp')+_cases('hp',2)+_parts('hp_witness_witness',3)
            +_call('beta_at_unique','x','x1','0','P','6')+('exact hp_witness_witness_right_left','exact hp_witness_witness_left'),
            'Functionality of the zero-th trace entry forces the actual empty product to be the Gaussian identity code.',
        ),
        spec(
            'gaussian_product_prefix_recode',f"forall b c d e l P. ({_product('b','c','l','P','recode_source')}) -> ({_preserve('b','c','d','e','l','recode_entries')}) -> ({_product('d','e','l','P','recode_target')})",
            (),_intro('b','c','d','e','l','P','hp','hpreserve')+_cases('hp',2)+_parts('hp_witness_witness',3)+_exists('x','x1')+('split','exact hp_witness_witness_left','split','exact hp_witness_witness_right_left')
            +_intro('i','hi')+(f"have hs : exists a R T. {_and(_at('b','c','i','a','recode_old_factor'),_at('x','x1','i','R','recode_old_before'),_at('x','x1','S i','T','recode_old_after'),_mul('R','a','T','recode_old_multiply'))}",)
            +_call('hp_witness_witness_right_right','i')+('exact hi',)+_cases('hs',3)+_parts('hs_witness_witness_witness',4)+_exists('x2','x3','x4')+('split',)
            +_call('hpreserve','i','x2')+('exact hi','exact hs_witness_witness_witness_left','split','exact hs_witness_witness_witness_right_left','split','exact hs_witness_witness_witness_right_right_left','exact hs_witness_witness_witness_right_right_right'),
            'Preserving actual factor entries preserves the same genuinely multiplied Gaussian product trace.',
        ),
        spec(
            'gaussian_product_successor_decompose',f"forall b c l Q. ({_product('b','c','S l','Q','successor_product')}) -> exists a P. "
            +_and(_at('b','c','l','a','successor_factor'),_product('b','c','l','P','successor_prefix'),_mul('P','a','Q','successor_multiply')),
            ('le_refl','beta_at_unique','gaussian_multiply_output_transport','lt_of_lt_of_le','le_succ_self'),
            _intro('b','c','l','Q','hp')+_cases('hp',2)+_parts('hp_witness_witness',3)
            +(f"have hs : exists a P T. {_and(_at('b','c','l','a','decompose_factor'),_at('x','x1','l','P','decompose_before'),_at('x','x1','S l','T','decompose_after'),_mul('P','a','T','decompose_multiply'))}",)
            +_call('hp_witness_witness_right_right','l')+_call('le_refl','S l')+_cases('hs',3)+_parts('hs_witness_witness_witness',4)
            +('have heq : x4=Q',)+_call('beta_at_unique','x','x1','S l','x4','Q')+('exact hs_witness_witness_witness_right_right_left','exact hp_witness_witness_right_left')
            +_exists('x2','x3')+('split','exact hs_witness_witness_witness_left','split')+_exists('x','x1')+('split','exact hp_witness_witness_left','split','exact hs_witness_witness_witness_right_left')
            +_intro('i','hi')+_call('hp_witness_witness_right_right','i')+_call('lt_of_lt_of_le','i','l','S l')+('exact hi',)+_call('le_succ_self','l')
            +_call('gaussian_multiply_output_transport','x3','x2','x4','Q')+('exact heq','exact hs_witness_witness_witness_right_right_right'),
            'Every nonempty actual Gaussian product exposes its final factor, the actual shorter prefix product, and the genuine final multiplication.',
        ),
    )


def _append_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    extension=_and(_at('h','e','S l','Q','append_trace_last'),_preserve('x','x1','h','e','S l','append_trace_prefix'))
    return (
        spec(
            'gaussian_product_successor_intro',f"forall b c l P a Q. ({_product('b','c','l','P','append_product_before')}) -> ({_at('b','c','l','a','append_factor')}) -> ({_mul('P','a','Q','append_multiply')}) -> ({_product('b','c','S l','Q','append_product_after')})",
            ('beta_prefix_extend','succ_le_succ','zero_le','finite_lt_succ_eq_or_lt','gaussian_product_beta_index_transport','le_refl','lt_of_lt_of_le','le_succ_self'),
            _intro('b','c','l','P','a','Q','hp','ha','hm')+_cases('hp',2)+_parts('hp_witness_witness',3)
            +(f"have hext : exists h e. ({extension})",)+_call('beta_prefix_extend','S l','x','x1','Q')+_cases('hext',2)+('cases hext_witness_witness',
              f"have hlast : ({_at('x2','x3','l','P','append_preserved_terminal')})")
            +_call('hext_witness_witness_right','l','P')+_call('le_refl','S l')+('exact hp_witness_witness_right_left',)
            +_exists('x2','x3')+('split',)+_call('hext_witness_witness_right','0','6')+_call('succ_le_succ','0','l')+_call('zero_le','l')+('exact hp_witness_witness_left','split','exact hext_witness_witness_left')
            +_intro('i','hi')+(f"have hc : i=l \\/ ({_lt('i','l','append_index_cases')})",)+_call('finite_lt_succ_eq_or_lt','l','i')+('exact hi','cases hc')
            +_exists('a','P','Q')+('split',)+_call('gaussian_product_beta_index_transport','b','c','l','i','a')+('symm','exact hc_left','exact ha','split')
            +_call('gaussian_product_beta_index_transport','x2','x3','l','i','P')+('symm','exact hc_left','exact hlast','split')
            +_call('gaussian_product_beta_index_transport','x2','x3','S l','S i','Q')+('congr','symm','exact hc_left','exact hext_witness_witness_left','exact hm',
              f"have hs : exists a R T. {_and(_at('b','c','i','a','append_old_factor'),_at('x','x1','i','R','append_old_before'),_at('x','x1','S i','T','append_old_after'),_mul('R','a','T','append_old_multiply'))}")
            +_call('hp_witness_witness_right_right','i')+('exact hc_right',)+_cases('hs',3)+_parts('hs_witness_witness_witness',4)
            +_exists('x4','x5','x6')+('split','exact hs_witness_witness_witness_left','split')+_call('hext_witness_witness_right','i','x5')
            +_call('lt_of_lt_of_le','i','l','S l')+('exact hc_right',)+_call('le_succ_self','l')+('exact hs_witness_witness_witness_right_left','split')
            +_call('hext_witness_witness_right','S i','x6')+_call('succ_le_succ','S i','l')+('exact hc_right','exact hs_witness_witness_witness_right_right_left','exact hs_witness_witness_witness_right_right_right'),
            'Append a genuine Gaussian multiplication step using a constructed beta extension of the product trace, preserving all previous steps.',
        ),
    )


def _product_value_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'gaussian_product_value_transport',f"forall b c l P Q. P=Q -> ({_product('b','c','l','P','value_transport_product')}) -> ({_product('b','c','l','Q','value_transport_result')})",
            (),_intro('b','c','l','P','Q','heq','h')+('rewrite heq at h',)*2+('exact h',),
            'Equality of actual canonical product values transports the endpoint of a real beta multiplication trace.',
        ),
        spec(
            'gaussian_product_length_transport',f"forall b c l m P. l=m -> ({_product('b','c','l','P','length_transport_product')}) -> ({_product('b','c','m','P','length_transport_result')})",
            (),_intro('b','c','l','m','P','heq','h')+('rewrite heq at h',)*3+('exact h',),
            'Equality of natural lengths transports the exact endpoint and bound of an actual Gaussian multiplication trace.',
        ),
        spec(
            'gaussian_product_functional',f"forall l b c P Q. ({_product('b','c','l','P','functional_first')}) -> ({_product('b','c','l','Q','functional_second')}) -> P=Q",
            ('gaussian_product_empty_value','gaussian_product_successor_decompose','beta_at_unique','gaussian_multiply_functional'),
            ('induction l',)+_intro('b','c','P','Q','hP','hQ')+('trans 6',)+_call('gaussian_product_empty_value','b','c','P')+('exact hP','have heq : Q=6')
            +_call('gaussian_product_empty_value','b','c','Q')+('exact hQ','symm','exact heq')
            +_intro('b','c','P','Q','hP','hQ')+(f"have hs : exists a R. {_and(_at('b','c','l','a','functional_first_factor'),_product('b','c','l','R','functional_first_prefix'),_mul('R','a','P','functional_first_multiply'))}",)
            +_call('gaussian_product_successor_decompose','b','c','l','P')+('exact hP',)+_cases('hs',2)+_parts('hs_witness_witness',3)
            +(f"have ht : exists a R. {_and(_at('b','c','l','a','functional_second_factor'),_product('b','c','l','R','functional_second_prefix'),_mul('R','a','Q','functional_second_multiply'))}",)
            +_call('gaussian_product_successor_decompose','b','c','l','Q')+('exact hQ',)+_cases('ht',2)+_parts('ht_witness_witness',3)
            +('have hfactor : x=x2',)+_call('beta_at_unique','b','c','l','x','x2')+('exact hs_witness_witness_left','exact ht_witness_witness_left','have hprefix : x1=x3')
            +_call('IH','b','c','x1','x3')+('exact hs_witness_witness_right_left','exact ht_witness_witness_right_left','rewrite hfactor at hs_witness_witness_right_right','rewrite hprefix at hs_witness_witness_right_right')
            +_call('gaussian_multiply_functional','x3','x2','P','Q')+('exact hs_witness_witness_right_right','exact ht_witness_witness_right_right'),
            'Two actual Gaussian multiplication traces on the same finite beta prefix have literally equal canonical endpoint codes.',
        ),
        spec(
            'gaussian_product_result_valid',f"forall l b c P. ({_product('b','c','l','P','product_result_valid')}) -> ({_valid('P','product_carrier')})",
            ('gaussian_product_empty_value','gaussian_one_valid','gaussian_product_successor_decompose','gaussian_multiply_output_valid'),
            ('induction l',)+_intro('b','c','P','hp')+('have heq : P=6',)+_call('gaussian_product_empty_value','b','c','P')+('exact hp','rewrite heq','exact gaussian_one_valid')
            +_intro('b','c','P','hp')+(f"have hs : exists a Q. {_and(_at('b','c','l','a','result_valid_factor'),_product('b','c','l','Q','result_valid_prefix'),_mul('Q','a','P','result_valid_multiply'))}",)
            +_call('gaussian_product_successor_decompose','b','c','l','P')+('exact hp',)+_cases('hs',2)+_parts('hs_witness_witness',3)
            +_call('gaussian_multiply_output_valid','x1','x','P')+('exact hs_witness_witness_right_right',),
            'Every actual finite Gaussian product has a valid carrier code, including the empty product.',
        ),
    )


def _factor_list_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'gaussian_irreducible_code_transport',f"forall p q. p=q -> ({_irreducible('p','irreducible_transport_source')}) -> ({_irreducible('q','irreducible_transport_target')})",
            (),_intro('p','q','heq','h')+('rewrite heq at h',)*4+('exact h',),
            'Literal equality of canonical Gaussian codes preserves the full actual-factorization irreducibility predicate.',
        ),
        spec(
            'gaussian_all_irreducible_prefix',f"forall b c l. ({_all_irreducible('b','c','S l','irreducible_full')}) -> ({_all_irreducible('b','c','l','irreducible_prefix')})",
            ('lt_of_lt_of_le','le_succ_self'),_intro('b','c','l','h','i','p','hi','hp')+_call('h','i','p')+_call('lt_of_lt_of_le','i','l','S l')+('exact hi',)+_call('le_succ_self','l')+('exact hp',),
            'Every shorter prefix of an actual all-irreducible Gaussian list remains all irreducible.',
        ),
        spec(
            'gaussian_all_irreducible_append',f"forall b c d e l p. ({_all_irreducible('b','c','l','append_irreducible_prefix')}) -> ({_preserve('b','c','d','e','l','append_irreducible_preserve')}) -> ({_at('d','e','l','p','append_irreducible_last')}) -> ({_irreducible('p','append_irreducible_factor')}) -> ({_all_irreducible('d','e','S l','append_irreducible_full')})",
            ('finite_lt_succ_eq_or_lt','beta_at_unique','gaussian_product_beta_index_transport','gaussian_irreducible_code_transport','factor_permutation_prefix_reflect'),
            _intro('b','c','d','e','l','p','hall','hpreserve','hlast','hp','i','q','hi','hq')+(f"have hc : i=l \\/ ({_lt('i','l','append_irreducible_index_cases')})",)
            +_call('finite_lt_succ_eq_or_lt','l','i')+('exact hi','cases hc','have heq : p=q')+_call('beta_at_unique','d','e','l','p','q')+('exact hlast',)
            +_call('gaussian_product_beta_index_transport','d','e','i','l','q')+('exact hc_left','exact hq')+_call('gaussian_irreducible_code_transport','p','q')+('exact heq','exact hp')
            +_call('hall','i','q')+('exact hc_right',)+_call('factor_permutation_prefix_reflect','b','c','d','e','l','i','q')+('exact hpreserve','exact hc_right','exact hq'),
            'Appending an actual irreducible Gaussian factor preserves all irreducible entries of the newly constructed beta prefix.',
        ),
        spec(
            'gaussian_unit_empty_factorization',f"forall z. ({_unit('z','unit_factorization_input')}) -> ({_factor('z','z','0','0','0','unit_factorization')})",
            ('gaussian_search_no_index_below_zero','gaussian_product_empty_exists','gaussian_multiply_one_right','gaussian_unit_valid'),
            _intro('z','hu')+('split','exact hu','split')+_intro('i','p','hi','hp')+('exfalso',)+_call('gaussian_search_no_index_below_zero','i')+('exact hi',)+_exists('6')+('split',)
            +_call('gaussian_product_empty_exists','0','0')+_call('gaussian_multiply_one_right','z')+_call('gaussian_unit_valid','z')+('exact hu',),
            'Every actual Gaussian unit is factored by its own unit code and an empty prime list, with the actual identity product.',
        ),
        spec(
            'gaussian_factorization_append_irreducible',f"forall z u b c l p w. ({_factor('z','u','b','c','l','factor_append_old')}) -> ({_irreducible('p','factor_append_prime')}) -> ({_mul('z','p','w','factor_append_equation')}) -> exists d e. ({_factor('w','u','d','e','S l','factor_append_new')})",
            ('beta_prefix_extend','gaussian_multiply_exists','gaussian_product_result_valid','gaussian_all_irreducible_append','gaussian_product_successor_intro','gaussian_product_prefix_recode','gaussian_multiply_associative'),
            _intro('z','u','b','c','l','p','w','hf','hp','hm')+_parts('hf',3)+('cases hf_right_right','cases hf_right_right_witness')+_parts('hp',4)
            +(f"have hext : exists d e. {_and(_at('d','e','l','p','factor_append_new_last'),_preserve('b','c','d','e','l','factor_append_new_prefix'))}",)
            +_call('beta_prefix_extend','l','b','c','p')+_cases('hext',2)+('cases hext_witness_witness',f"have hQ : exists Q. ({_mul('x','p','Q','factor_append_product')})")
            +_call('gaussian_multiply_exists','x','p')+_call('gaussian_product_result_valid','l','b','c','x')+('exact hf_right_right_witness_left',f"exact {_part('hp',4,0)}",'cases hQ')
            +_exists('x1','x2')+('split','exact hf_left','split')+_call('gaussian_all_irreducible_append','b','c','x1','x2','l','p')+('exact hf_right_left','exact hext_witness_witness_right','exact hext_witness_witness_left','exact hp')
            +_exists('x3')+('split',)+_call('gaussian_product_successor_intro','x1','x2','l','x','p','x3')+_call('gaussian_product_prefix_recode','b','c','x1','x2','l','x')+('exact hf_right_right_witness_left','exact hext_witness_witness_right','exact hext_witness_witness_left','exact hQ_witness')
            +_call('gaussian_multiply_associative','u','x','p','z','x3','w')+('exact hf_right_right_witness_right','exact hm','exact hQ_witness'),
            'Construct and verify a longer Gaussian prime-factor list by appending one actual irreducible factor while retaining the actual leading unit.',
        ),
    )


def _existence_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    result='exists u b c l. '+_factor('z','u','b','c','l','factorization_exists')
    return (
        spec(
            'gaussian_irreducible_factorization_bounded_norm',f"forall k z N. ({_le('N','k','factorization_bound')}) -> ({_norm('z','N','factorization_norm')}) -> ~(z=0) -> ({result})",
            ('le_zero','gaussian_norm_zero_implies_code_zero','gaussian_norm_value_transport','gaussian_unit_decidable','gaussian_norm_input_valid','gaussian_unit_empty_factorization','gaussian_irreducible_factor_reduction','le_of_succ_le_succ','lt_of_lt_of_le','gaussian_factorization_append_irreducible','gaussian_multiply_commutative'),
            ('induction k',)+_intro('z','N','hb','hn','hz')+('exfalso','apply hz')+_call('gaussian_norm_zero_implies_code_zero','z')+_call('gaussian_norm_value_transport','z','N','0')+_call('le_zero','N')+('exact hb','exact hn')
            +_intro('z','N','hb','hn','hz')+(f"have hu : ({_unit('z','factorization_unit_yes')}) \\/ ~({_unit('z','factorization_unit_no')})",)
            +_call('gaussian_unit_decidable','z')+_call('gaussian_norm_input_valid','z','N')+('exact hn','cases hu')+_exists('z','0','0','0')+_call('gaussian_unit_empty_factorization','z')+('exact hu_left',
              f"have hr : exists p q Q. {_and(_irreducible('p','factorization_step_prime'),_mul('p','q','z','factorization_step_product'),_norm('q','Q','factorization_step_norm'),_lt('Q','N','factorization_step_strict'),'~(q=0)')}")
            +_call('gaussian_irreducible_factor_reduction','z','N')+('exact hn','exact hz','exact hu_right')+_cases('hr',3)+_parts('hr_witness_witness_witness',5)
            +(f"have hrec : exists u b c l. ({_factor('x1','u','b','c','l','factorization_recursive')})",)+_call('IH','x1','x2')+_call('le_of_succ_le_succ','x2','k')
            +_call('lt_of_lt_of_le','x2','N','S k')+(f"exact {_part('hr_witness_witness_witness',5,3)}",'exact hb',f"exact {_part('hr_witness_witness_witness',5,2)}",f"exact {_part('hr_witness_witness_witness',5,4)}")+_cases('hrec',4)
            +(f"have hext : exists d e. ({_factor('z','x3','d','e','S x6','factorization_extended')})",)
            +_call('gaussian_factorization_append_irreducible','x1','x3','x4','x5','x6','x','z')+('exact hrec_witness_witness_witness_witness',f"exact {_part('hr_witness_witness_witness',5,0)}")
            +_call('gaussian_multiply_commutative','x','x1','z')+(f"exact {_part('hr_witness_witness_witness',5,1)}",)+_cases('hext',2)
            +_exists('x3','x7','x8','S x6')+('exact hext_witness_witness',),
            'Construct a genuine finite irreducible Gaussian factorization by ordinary norm induction; each recursive quotient has strictly smaller proved norm.',
        ),
        spec(
            'gaussian_irreducible_factorization_exists',f"forall z. ({_valid('z','factorization_domain')}) -> ~(z=0) -> ({result})",
            ('gaussian_norm_exists','gaussian_irreducible_factorization_bounded_norm','le_refl'),
            _intro('z','hv','hz')+(f"have hn : exists N. ({_norm('z','N','factorization_actual_norm')})",)+_call('gaussian_norm_exists','z')+('exact hv','cases hn')
            +_call('gaussian_irreducible_factorization_bounded_norm','x','z','x')+_call('le_refl','x')+('exact hn_witness','exact hz'),
            'Every actual nonzero Gaussian integer has an actual unit coefficient and an actually multiplied finite list of irreducible factors, including every unit boundary.',
        ),
        spec(
            'gaussian_irreducible_factorization_is_prime',f"forall z u b c l. ({_factor('z','u','b','c','l','irreducible_factorization_given')}) -> ({_prime_factor('z','u','b','c','l','prime_factorization_result')})",
            ('gaussian_irreducible_is_prime',),_intro('z','u','b','c','l','hf')+_parts('hf',3)+('split','exact hf_left','split')+_intro('i','p','hi','hp')
            +_call('gaussian_irreducible_is_prime','p')+_call('hf_right_left','i','p')+('exact hi','exact hp','exact hf_right_right'),
            'Every listed Gaussian irreducible is an actual prime divisor by the checked Bezout theorem, with the unit and product trace unchanged.',
        ),
        spec(
            'gaussian_prime_factorization_is_irreducible',f"forall z u b c l. ({_prime_factor('z','u','b','c','l','prime_factorization_given')}) -> ({_factor('z','u','b','c','l','irreducible_factorization_result')})",
            ('gaussian_prime_is_irreducible',),_intro('z','u','b','c','l','hf')+_parts('hf',3)+('split','exact hf_left','split')+_intro('i','p','hi','hp')
            +_call('gaussian_prime_is_irreducible','p')+_call('hf_right_left','i','p')+('exact hi','exact hp','exact hf_right_right'),
            'The actual Gaussian prime-divisor graph implies irreducibility, so the two finite factorization specifications are equivalent.',
        ),
        spec(
            'gaussian_prime_factorization_exists',f"forall z. ({_valid('z','prime_factorization_domain')}) -> ~(z=0) -> exists u b c l. ({_prime_factor('z','u','b','c','l','prime_factorization_exists')})",
            ('gaussian_irreducible_factorization_exists','gaussian_irreducible_factorization_is_prime'),
            _intro('z','hv','hz')+(f"have hf : {result}",)+_call('gaussian_irreducible_factorization_exists','z')+('exact hv','exact hz')+_cases('hf',4)
            +_exists('x','x1','x2','x3')+_call('gaussian_irreducible_factorization_is_prime','z','x','x1','x2','x3')+('exact hf_witness_witness_witness_witness',),
            'Every actual nonzero Gaussian integer has a genuine finite RingPrime factorization, not merely a conditional gcd or a supplied factor-list certificate.',
        ),
    )


def _list_product_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'gaussian_all_irreducible_length_transport',f"forall b c l m. l=m -> ({_all_irreducible('b','c','l','irreducible_length_old')}) -> ({_all_irreducible('b','c','m','irreducible_length_new')})",
            (),_intro('b','c','l','m','heq','h')+('rewrite heq at h','exact h'),
            'Equality of lengths transports the exact finite bound of an all-irreducible Gaussian factor prefix.',
        ),
        spec(
            'gaussian_all_irreducible_product_exists',f"forall l b c. ({_all_irreducible('b','c','l','all_irreducible_product_input')}) -> exists P. ({_product('b','c','l','P','all_irreducible_product_exists')})",
            ('gaussian_product_empty_exists','gaussian_all_irreducible_prefix','beta_at_exists','le_refl','gaussian_multiply_exists','gaussian_product_result_valid','gaussian_product_successor_intro'),
            ('induction l',)+_intro('b','c','hall')+_exists('6')+_call('gaussian_product_empty_exists','b','c')
            +_intro('b','c','hall')+(f"have hp : exists P. ({_product('b','c','l','P','all_product_prefix')})",)+_call('IH','b','c')+_call('gaussian_all_irreducible_prefix','b','c','l')+('exact hall','cases hp',
              f"have ha : exists a. ({_at('b','c','l','a','all_product_last')})")
            +_call('beta_at_exists','b','c','l')+('cases ha',f"have hir : ({_irreducible('x1','all_product_irreducible_last')})")+_call('hall','l','x1')+_call('le_refl','S l')+('exact ha_witness',)+_parts('hir',4)
            +(f"have hq : exists Q. ({_mul('x','x1','Q','all_product_successor')})",)+_call('gaussian_multiply_exists','x','x1')+_call('gaussian_product_result_valid','l','b','c','x')+('exact hp_witness','exact hir_left','cases hq')
            +_exists('x2')+_call('gaussian_product_successor_intro','b','c','l','x','x1','x2')+('exact hp_witness','exact ha_witness','exact hq_witness'),
            'Construct an actual Gaussian product trace for every all-irreducible beta prefix, including empty prefixes and repeated associate factors.',
        ),
        spec(
            'gaussian_all_irreducible_product_nonzero',f"forall l b c P. ({_all_irreducible('b','c','l','nonzero_product_factors')}) -> ({_product('b','c','l','P','nonzero_product_trace')}) -> ~(P=0)",
            ('gaussian_product_empty_value','gaussian_product_successor_decompose','gaussian_all_irreducible_prefix','gaussian_multiply_zero_implies_zero_factor','le_refl'),
            ('induction l',)+_intro('b','c','P','hall','hp','hz')+('have hid : P=6',)+_call('gaussian_product_empty_value','b','c','P')+('exact hp','have hbad : 6=0','trans P','symm','exact hid','exact hz','apply PA1','exact hbad')
            +_intro('b','c','P','hall','hp','hz')+(f"have hs : exists a Q. {_and(_at('b','c','l','a','nonzero_product_last'),_product('b','c','l','Q','nonzero_product_prefix'),_mul('Q','a','P','nonzero_product_step'))}",)
            +_call('gaussian_product_successor_decompose','b','c','l','P')+('exact hp',)+_cases('hs',2)+_parts('hs_witness_witness',3)
            +('have hcases : x1=0 \\/ x=0',)+_call('gaussian_multiply_zero_implies_zero_factor','x1','x')+('rewrite hz at hs_witness_witness_right_right','exact hs_witness_witness_right_right','cases hcases')
            +_call('IH','b','c','x1')+_call('gaussian_all_irreducible_prefix','b','c','l')+('exact hall','exact hs_witness_witness_right_left','exact hcases_left',f"have hir : ({_irreducible('x','nonzero_last_irreducible')})")
            +_call('hall','l','x')+_call('le_refl','S l')+('exact hs_witness_witness_left',)+_parts('hir',4)+('apply hir_right_left','exact hcases_right'),
            'A finite product of actual irreducible Gaussian factors is nonzero, by the proved absence of Gaussian zero divisors and the genuine empty product.',
        ),
        spec(
            'gaussian_all_irreducible_product_unit_length_zero',f"forall b c l P. ({_all_irreducible('b','c','l','unit_product_factors')}) -> ({_product('b','c','l','P','unit_product_trace')}) -> ({_unit('P','unit_product_unit')}) -> l=0",
            ('zero_or_succ','gaussian_product_length_transport','gaussian_all_irreducible_length_transport','gaussian_product_successor_decompose','le_refl','gaussian_unit_factor_right'),
            _intro('b','c','l','P','hall','hp','hu')+('have hc : l=0 \\/ exists k. l=S k',)+_call('zero_or_succ','l')+('cases hc','exact hc_left','cases hc_right',
              f"have hpnew : ({_product('b','c','S x','P','unit_product_nonempty')})")
            +_call('gaussian_product_length_transport','b','c','l','S x','P')+('exact hc_right_witness','exact hp',f"have hanew : ({_all_irreducible('b','c','S x','unit_product_nonempty_factors')})")
            +_call('gaussian_all_irreducible_length_transport','b','c','l','S x')+('exact hc_right_witness','exact hall',
              f"have hs : exists a Q. {_and(_at('b','c','x','a','unit_product_last'),_product('b','c','x','Q','unit_product_prefix'),_mul('Q','a','P','unit_product_step'))}")
            +_call('gaussian_product_successor_decompose','b','c','x','P')+('exact hpnew',)+_cases('hs',2)+_parts('hs_witness_witness',3)
            +(f"have hir : ({_irreducible('x1','unit_product_last_irreducible')})",)+_call('hanew','x','x1')+_call('le_refl','S x')+('exact hs_witness_witness_left',)+_parts('hir',4)
            +('exfalso','apply hir_right_right_left')+_call('gaussian_unit_factor_right','x2','x1','P')+('exact hs_witness_witness_right_right','exact hu'),
            'An actual all-irreducible Gaussian product is a unit only at length zero; no nonempty unit factorization is allowed by the arithmetic.',
        ),
        spec(
            'gaussian_factorization_value_valid',f"forall z u b c l. ({_factor('z','u','b','c','l','factor_valid_given')}) -> ({_valid('z','factor_valid_value')})",
            ('gaussian_multiply_output_valid',),_intro('z','u','b','c','l','hf')+_parts('hf',3)+('cases hf_right_right','cases hf_right_right_witness')
            +_call('gaussian_multiply_output_valid','u','x','z')+('exact hf_right_right_witness_right',),
            'Every actual Gaussian factorization reconstructs a value in the genuine canonical carrier.',
        ),
        spec(
            'gaussian_factorization_value_nonzero',f"forall z u b c l. ({_factor('z','u','b','c','l','factor_nonzero_given')}) -> ~(z=0)",
            ('gaussian_multiply_zero_implies_zero_factor','gaussian_unit_nonzero','gaussian_all_irreducible_product_nonzero'),
            _intro('z','u','b','c','l','hf','hz')+_parts('hf',3)+('cases hf_right_right','cases hf_right_right_witness','have hcases : u=0 \\/ x=0')
            +_call('gaussian_multiply_zero_implies_zero_factor','u','x')+('rewrite hz at hf_right_right_witness_right','exact hf_right_right_witness_right','cases hcases')
            +_call('gaussian_unit_nonzero','u')+('exact hf_left','exact hcases_left')+_call('gaussian_all_irreducible_product_nonzero','l','b','c','x')+('exact hf_right_left','exact hf_right_right_witness_left','exact hcases_right'),
            'The actual unit coefficient and actual irreducible product prevent any Gaussian factorization of zero.',
        ),
        spec(
            'gaussian_irreducible_divisor_product_member',f"forall l b c P p. ({_all_irreducible('b','c','l','member_factors')}) -> ({_product('b','c','l','P','member_trace')}) -> ({_irreducible('p','member_prime')}) -> ({_dvd('p','P','member_divisor')}) -> exists i q. "
            +_and(_lt('i','l','member_index'),_at('b','c','i','q','member_factor'),gr._associate('p','q','member_association')),
            ('gaussian_product_empty_value','gaussian_divisor_of_unit_is_unit','gaussian_one_unit','gaussian_product_successor_decompose','gaussian_irreducible_dvd_product','gaussian_all_irreducible_prefix','lt_of_lt_of_le','le_succ_self','le_refl','gaussian_irreducible_divides_irreducible_associate'),
            ('induction l',)+_intro('b','c','P','p','hall','hP','hir','hd')+_parts('hir',4)+('have heq : P=6',)+_call('gaussian_product_empty_value','b','c','P')+('exact hP','exfalso','apply hir_right_right_left')
            +_call('gaussian_divisor_of_unit_is_unit','p','6')+('rewrite heq at hd','exact hd','exact gaussian_one_unit')
            +_intro('b','c','P','p','hall','hP','hir','hd')+(f"have hs : exists a Q. {_and(_at('b','c','l','a','member_last'),_product('b','c','l','Q','member_prefix'),_mul('Q','a','P','member_step'))}",)
            +_call('gaussian_product_successor_decompose','b','c','l','P')+('exact hP',)+_cases('hs',2)+_parts('hs_witness_witness',3)
            +(f"have hc : ({_dvd('p','x1','member_prefix_divisor')}) \\/ ({_dvd('p','x','member_last_divisor')})",)+_call('gaussian_irreducible_dvd_product','p','x1','x','P')+('exact hir','exact hs_witness_witness_right_right','exact hd','cases hc',
              f"have hrec : exists i q. {_and(_lt('i','l','member_recursive_index'),_at('b','c','i','q','member_recursive_factor'),gr._associate('p','q','member_recursive_association'))}")
            +_call('IH','b','c','x1','p')+_call('gaussian_all_irreducible_prefix','b','c','l')+('exact hall','exact hs_witness_witness_right_left','exact hir','exact hc_left')+_cases('hrec',2)+_parts('hrec_witness_witness',3)
            +_exists('x2','x3')+('split',)+_call('lt_of_lt_of_le','x2','l','S l')+('exact hrec_witness_witness_left',)+_call('le_succ_self','l')+('split','exact hrec_witness_witness_right_left','exact hrec_witness_witness_right_right')
            +_exists('l','x')+('split',)+_call('le_refl','S l')+('split','exact hs_witness_witness_left')+_call('gaussian_irreducible_divides_irreducible_associate','p','x')+('exact hir',)
            +_call('hall','l','x')+_call('le_refl','S l')+('exact hs_witness_witness_left','exact hc_right'),
            'Find an actual occurrence associated to an irreducible divisor in any finite irreducible Gaussian product, using the proved prime-divisor product theorem at every step.',
        ),
    )


def make_gaussian_factorization_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return _basic_product_rows(spec)+_append_rows(spec)+_product_value_rows(spec)+_factor_list_rows(spec)+_existence_rows(spec)+_list_product_rows(spec)
