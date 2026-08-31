"""Actual leading-zero removal from highest-degree-first coefficient prefixes.

The input length is split into a removed zero prefix and an actually encoded
suffix.  The suffix is empty or has a decoded nonzero first coefficient.
Neither a degree, a trimming witness nor a polynomial identity is assumed by
the construction.  Canonical input coefficients suffice at every modulus;
primality is not needed.  Uniqueness concerns lengths and decoded coefficients,
never the two natural numbers used as a beta encoding.
"""

from __future__ import annotations

from typing import Any, Callable

from .matrix_coded_product_candidate import _slice_terms
from .prime_field_arithmetic_candidate import _and, _call, _intro, _lt, _parts, _public
from .prime_field_polynomial_candidate import _at, _coeff, _equal, _repeat
from .prime_field_polynomial_degree_candidate import _degree
from .prime_field_tables_candidate import _rewrite_all


def _le(a: str, b: str, tag: str) -> str:
    return f"exists pftrim_gap_{tag}. pftrim_gap_{tag}+({a})=({b})"


def _suffix(b: str, c: str, t: str, d: str, e: str, length: str, tag: str) -> str:
    i, a = f"pftrim_index_{tag}", f"pftrim_value_{tag}"
    return (
        f"forall {i} {a}. ({_lt(i,length,tag+'bound')}) -> "
        f"({_at(b,c,f'({t})+{i}',a,tag+'source')}) -> "
        f"({_at(d,e,i,a,tag+'output')})"
    )


def _head(b: str, c: str, i: str, tag: str) -> str:
    a = f"pftrim_leading_{tag}"
    return f"exists {a}. " + _and(_at(b,c,i,a,tag+'entry'), f"~({a}=0)")


def _cut(b: str, c: str, length: str, t: str, m: str, tag: str) -> str:
    terminal = f"({m})=0 \\/ ({_and(f'~(({m})=0)',_head(b,c,t,tag+'head'))})"
    return _and(f"({length})=({t})+({m})", _repeat(b,c,'0',t,tag+'zero'), terminal)


def _trim(p: str, b: str, c: str, length: str, t: str,
          d: str, e: str, m: str, tag: str) -> str:
    return _and(
        f"({length})=({t})+({m})",
        _coeff(p,b,c,length,tag+'input'),
        _repeat(b,c,'0',t,tag+'removed'),
        _suffix(b,c,t,d,e,m,tag+'suffix'),
        f"({m})=0 \\/ ({_head(d,e,'0',tag+'normal')})",
    )


def prime_field_polynomial_suffix_relation(b: str, c: str, t: str,
        d: str, e: str, length: str, *, tag: str, variables: tuple[str, ...]) -> str:
    """Actual decoded suffix at offset t, with no values imposed past length."""
    return _public(_suffix, (b,c,t,d,e,length), tag=tag, variables=variables)


def prime_field_polynomial_trim_relation(p: str, b: str, c: str, length: str,
        t: str, d: str, e: str, m: str, *, tag: str, variables: tuple[str, ...]) -> str:
    """Canonical input, removed zero prefix, actual suffix, and normalized head."""
    return _public(_trim, (p,b,c,length,t,d,e,m), tag=tag, variables=variables)


PARAMETERS = ('p','b','c','L','t','d','e','M')


def _suffix_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    body = _intro('b','c','t','M')
    body += (f"have hs : exists d e. ({_slice_terms('b','c','t','1','d','e','M',tag='trim_suffix_actual')})",)
    body += _call('beta_affine_matrix_slice_exists','b','c','t','1','M')
    body += ('cases hs','cases hs_witness','exists x','exists x1') + _intro('i','a','hi','ha')
    body += (f"have hz : exists z. ({_at('x','x1','i','z','suffix_output')})",)
    body += _call('beta_at_exists','x','x1','i') + ('cases hz','have heq : x2=a')
    body += _call('hs_witness_witness','i','a','x2') + ('exact hi','have hindex : t+1*i=t+i','simp [one_mul]')
    body += ('rewrite hindex','rewrite hindex','exact ha','exact hz_witness')
    body += _rewrite_all('heq',_at('x','x1','i','x2','suffix_rewrite'),'x2','hz_witness') + ('exact hz_witness',)
    exists = spec(
        'prime_field_polynomial_suffix_exists',
        f"forall b c t M. exists d e. ({_suffix('b','c','t','d','e','M','suffix_exists')})",
        ('beta_affine_matrix_slice_exists','beta_at_exists','one_mul'), body,
        'Construct every finite beta-coded suffix by the existing actual affine-slice constructor at stride one, including length zero.',
    )
    entry = spec(
        'prime_field_polynomial_suffix_entry',
        f"forall b c t d e M i a r. ({_suffix('b','c','t','d','e','M','suffix_entry')}) -> "
        f"({_lt('i','M','suffix_entry_bound')}) -> ({_at('b','c','t+i','a','suffix_entry_source')}) -> "
        f"({_at('d','e','i','r','suffix_entry_output')}) -> r=a",
        ('beta_at_unique',),
        _intro('b','c','t','d','e','M','i','a','r','h','hi','ha','hr')
        + _call('beta_at_unique','d','e','i','r','a') + ('exact hr',)
        + _call('h','i','a') + ('exact hi','exact ha'),
        'Every actual output decoding equals the input coefficient at the supplied shifted index.',
    )
    body = _intro(*PARAMETERS,'hlen','hc','hs','i','hi')
    body += (f"have hshift : {_lt('t+i','L','suffix_shift_bound')}",'rewrite hlen')
    body += _call('matrix_recursive_lt_add_left','i','M','t') + ('exact hi',)
    body += (f"have ha : exists a. {_and(_at('b','c','t+i','a','suffix_bounded_source'),_lt('a','p','suffix_bounded_value'))}",)
    body += _call('hc','t+i') + ('exact hshift','cases ha','cases ha_witness','exists x','split')
    body += _call('hs','i','x') + ('exact hi','exact ha_witness_left','exact ha_witness_right')
    bounded = spec(
        'prime_field_polynomial_suffix_bounded',
        f"forall {' '.join(PARAMETERS)}. L=t+M -> ({_coeff('p','b','c','L','suffix_input_coefficients')}) -> "
        f"({_suffix('b','c','t','d','e','M','suffix_bounded')}) -> ({_coeff('p','d','e','M','suffix_output_coefficients')})",
        ('matrix_recursive_lt_add_left',), body,
        'A genuine suffix ending at the annotated input length inherits every canonical coefficient bound.',
    )
    body = _intro('b','c','t','d','e','f','g','M','hd','hf','i','a','hi','ha')
    body += (f"have hz : exists z. ({_at('b','c','t+i','z','suffix_equal_source')})",)
    body += _call('beta_at_exists','b','c','t+i') + ('cases hz','have heq : a=x')
    body += _call('beta_at_unique','d','e','i','a','x') + ('exact ha',)
    body += _call('hd','i','x') + ('exact hi','exact hz_witness')
    body += _rewrite_all('heq',_at('f','g','i','a','suffix_equal_target'),'a')
    body += _call('hf','i','x') + ('exact hi','exact hz_witness')
    equal = spec(
        'prime_field_polynomial_suffix_equal',
        f"forall b c t d e f g M. ({_suffix('b','c','t','d','e','M','suffix_equal_left')}) -> "
        f"({_suffix('b','c','t','f','g','M','suffix_equal_right')}) -> ({_equal('d','e','f','g','M','suffix_equal_result')})",
        ('beta_at_exists','beta_at_unique'), body,
        'Two actual suffix encodings agree at every decoded prefix position, without asserting equality of raw codes.',
    )
    return exists, entry, bounded, equal


def _construction_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    old = 'hold_witness_witness'
    body = _intro('b','c') + ('induction L','exists 0','exists 0','split','simp','split')
    body += _call('beta_repeat_empty','b','c','0','0') + ('refl','left','refl')
    body += (f"have hold : exists t M. ({_cut('b','c','L','t','M','cut_previous')})",'exact IH','cases hold','cases hold_witness')
    body += _parts(old,3) + ('cases '+old+'_right_right','have hlen : L=x','trans x+x1',f'exact {old}_left',f'rewrite {old}_right_right_left','simp')
    body += (f"have hzero : {_repeat('b','c','0','L','cut_zero_old')}",'rewrite hlen',f'exact {old}_right_left')
    body += (f"have ha : exists a. ({_at('b','c','L','a','cut_last')})",)
    body += _call('beta_at_exists','b','c','L') + ('cases ha','have hz : x2=0 \\/ ~(x2=0)')
    body += _call('eq_decidable','x2','0') + ('cases hz','exists S L','exists 0','split','simp','split')
    body += _intro('i','hi') + (f"have hindex : i=L \\/ ({_lt('i','L','cut_old_index')})",)
    body += _call('finite_lt_succ_eq_or_lt','L','i') + ('exact hi','cases hindex')
    body += _rewrite_all('hindex_left',_at('b','c','i','0','cut_zero_last'),'i')
    body += _rewrite_all('hz_left',_at('b','c','L','x2','cut_zero_last_source'),'x2','ha_witness') + ('exact ha_witness',)
    body += _call('hzero','i') + ('exact hindex_right','left','refl')
    body += ('exists L','exists 1','split','simp','split','exact hzero','right','split','intro hbad')
    body += _call('succ_ne_zero','0') + ('exact hbad','exists x2','split','exact ha_witness','exact hz_right')
    body += ('cases '+old+'_right_right_right','exists x','exists S x1','split','trans S (x+x1)','congr',f'exact {old}_left','symm','apply PA4','split',f'exact {old}_right_left','right','split','intro hbad')
    body += _call('succ_ne_zero','x1') + ('exact hbad',f'exact {old}_right_right_right_right')
    cut = spec(
        'prime_field_polynomial_leading_zero_cut_exists',
        f"forall b c L. exists t M. ({_cut('b','c','L','t','M','cut_exists')})",
        ('beta_repeat_empty','beta_at_exists','eq_decidable','finite_lt_succ_eq_or_lt','succ_ne_zero'), body,
        'Finite induction scans actual decoded coefficients: either the entire prefix is zero or the first retained position has an actual nonzero value.',
    )
    body = _intro(*PARAMETERS,'hc','hcut','hs') + _parts('hcut',3)
    body += ('split','exact hcut_left','split','exact hc','split','exact hcut_right_left','split','exact hs','cases hcut_right_right','left','exact hcut_right_right_left','right','cases hcut_right_right_right','cases hcut_right_right_right_right','cases hcut_right_right_right_right_witness','exists x','split')
    body += _call('hs','0','x') + _call('one_le_of_ne_zero','M') + ('exact hcut_right_right_right_left','have hindex : t+0=t','simp','rewrite hindex','rewrite hindex','exact hcut_right_right_right_right_witness_left','exact hcut_right_right_right_right_witness_right')
    from_cut = spec(
        'prime_field_polynomial_trim_from_cut',
        f"forall {' '.join(PARAMETERS)}. ({_coeff('p','b','c','L','cut_to_trim_coefficients')}) -> "
        f"({_cut('b','c','L','t','M','cut_to_trim_source')}) -> ({_suffix('b','c','t','d','e','M','cut_to_trim_suffix')}) -> "
        f"({_trim(*PARAMETERS,'cut_to_trim_result')})",
        ('one_le_of_ne_zero',), body,
        'An actually constructed first-nonzero cut and actual suffix supply the normalized output head; no output-bound or algebra-law premise is assumed.',
    )
    body = _intro('p','b','c','L','hc') + (f"have hcut : exists t M. ({_cut('b','c','L','t','M','trim_exists_cut')})",)
    body += _call('prime_field_polynomial_leading_zero_cut_exists','b','c','L') + ('cases hcut','cases hcut_witness')
    body += (f"have hs : exists d e. ({_suffix('b','c','x','d','e','x1','trim_exists_suffix')})",)
    body += _call('prime_field_polynomial_suffix_exists','b','c','x','x1') + ('cases hs','cases hs_witness','exists x','exists x2','exists x3','exists x1')
    body += _call('prime_field_polynomial_trim_from_cut','p','b','c','L','x','x2','x3','x1')
    body += ('exact hc','exact hcut_witness_witness','exact hs_witness_witness')
    exists = spec(
        'prime_field_polynomial_trim_exists',
        f"forall p b c L. ({_coeff('p','b','c','L','trim_exists_source')}) -> exists t d e M. ({_trim(*PARAMETERS,'trim_exists_result')})",
        ('prime_field_polynomial_leading_zero_cut_exists','prime_field_polynomial_suffix_exists','prime_field_polynomial_trim_from_cut'), body,
        'Every actual canonical input has a genuinely beta-coded leading-zero trim, for all moduli and all finite lengths including zero.',
    )
    empty = spec(
        'prime_field_polynomial_trim_empty_input',
        f"forall p b c d e. ({_trim('p','b','c','0','0','d','e','0','empty_trim')})",
        ('matrix_rank_bounded_prefix_empty','beta_repeat_empty','matrix_rank_no_index_below_zero'),
        _intro('p','b','c','d','e') + ('split','simp','split')
        + _call('matrix_rank_bounded_prefix_empty','b','c','p') + ('split',)
        + _call('beta_repeat_empty','b','c','0','0') + ('refl','split')
        + _intro('i','a','hi','ha') + ('exfalso',) + _call('matrix_rank_no_index_below_zero','i')
        + ('exact hi','left','refl'),
        'Every pair of output beta codes is a valid empty trim of every empty input, including modulus zero; raw encodings are deliberately unconstrained.',
    )
    return cut, from_cut, exists, empty


def _consequence_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    body = _intro(*PARAMETERS,'h') + _parts('h',5)
    body += _call('prime_field_polynomial_suffix_bounded',*PARAMETERS)
    body += ('exact h_left','exact h_right_left','exact h_right_right_right_left')
    bounded = spec(
        'prime_field_polynomial_trim_output_coefficients',
        f"forall {' '.join(PARAMETERS)}. ({_trim(*PARAMETERS,'trim_bounded_source')}) -> ({_coeff('p','d','e','M','trim_bounded_result')})",
        ('prime_field_polynomial_suffix_bounded',), body,
        'The actual trimmed coefficients are canonical below the same modulus; this is a consequence, not a clause assumed in Trim.',
    )
    bounds = spec(
        'prime_field_polynomial_trim_length_bounds',
        f"forall {' '.join(PARAMETERS)}. ({_trim(*PARAMETERS,'trim_length_source')}) -> {_and(_le('t','L','removed_bound'),_le('M','L','retained_bound'))}",
        ('add_comm',),
        _intro(*PARAMETERS,'h') + _parts('h',5)
        + ('split','exists M','trans t+M','apply add_comm','symm','exact h_left','exists t','symm','exact h_left'),
        'Both the number of removed leading zeroes and the retained length are bounded by the actual annotated input length.',
    )
    body = _intro(*PARAMETERS,'a','h','hM','ha') + _parts('h',5)
    body += ('cases h_right_right_right_right','exfalso','apply hM','exact h_right_right_right_right_left','cases h_right_right_right_right_right','cases h_right_right_right_right_right_witness')
    body += (f"have hout : {_at('d','e','0','a','trim_head_transported')}",)
    body += _call('h_right_right_right_left','0','a') + _call('one_le_of_ne_zero','M')
    body += ('exact hM','have hindex : t+0=t','simp','rewrite hindex','rewrite hindex','exact ha','have heq : a=x')
    body += _call('beta_at_unique','d','e','0','a','x') + ('exact hout','exact h_right_right_right_right_right_witness_left','intro hz','apply h_right_right_right_right_right_witness_right','trans a','symm','exact heq','exact hz')
    head = spec(
        'prime_field_polynomial_trim_leading_source_nonzero',
        f"forall {' '.join(PARAMETERS)} a. ({_trim(*PARAMETERS,'trim_nonzero_source')}) -> ~(M=0) -> "
        f"({_at('b','c','t','a','trim_leading_input')}) -> ~(a=0)",
        ('one_le_of_ne_zero','beta_at_unique'), body,
        'When the retained length is positive, every actual input decoding at the cut position is nonzero.',
    )
    zero = spec(
        'prime_field_polynomial_trim_zero_of_empty',
        f"forall {' '.join(PARAMETERS)}. ({_trim(*PARAMETERS,'trim_empty_source')}) -> M=0 -> ({_repeat('b','c','0','L','trim_zero_input')})",
        (),
        _intro(*PARAMETERS,'h','hM') + _parts('h',5)
        + ('have hlen : L=t','trans t+M','exact h_left','rewrite hM','simp','rewrite hlen','exact h_right_right_left'),
        'An empty actual trim certifies that every coefficient of the entire input prefix is zero.',
    )
    body = _intro(*PARAMETERS,'h','hz') + ('have hM : M=0 \\/ ~(M=0)',)
    body += _call('eq_decidable','M','0') + ('cases hM','exact hM_left',f"have hcopy : {_trim(*PARAMETERS,'trim_zero_copy')}",'exact h')
    body += _parts('hcopy',5) + (f"have ht : {_lt('t+0','L','trim_zero_cut_bound')}",'rewrite hcopy_left')
    body += _call('matrix_recursive_lt_add_left','0','M','t') + _call('one_le_of_ne_zero','M') + ('exact hM_right','have hindex : t+0=t','simp','rewrite hindex at ht')
    body += (f"have hat : {_at('b','c','t','0','trim_zero_cut_entry')}",) + _call('hz','t') + ('exact ht','exfalso')
    body += _call('prime_field_polynomial_trim_leading_source_nonzero',*PARAMETERS,'0') + ('exact h','exact hM_right','exact hat','refl')
    empty = spec(
        'prime_field_polynomial_trim_empty_of_zero',
        f"forall {' '.join(PARAMETERS)}. ({_trim(*PARAMETERS,'trim_all_zero')}) -> ({_repeat('b','c','0','L','trim_all_zero_input')}) -> M=0",
        ('eq_decidable','matrix_recursive_lt_add_left','one_le_of_ne_zero','prime_field_polynomial_trim_leading_source_nonzero'), body,
        'A genuinely all-zero input cannot have a nonempty normalized trim, proved using actual input and output beta values.',
    )
    iff = spec(
        'prime_field_polynomial_trim_zero_iff',
        f"forall {' '.join(PARAMETERS)}. ({_trim(*PARAMETERS,'trim_zero_equivalence')}) -> "
        + _and(f"M=0 -> ({_repeat('b','c','0','L','trim_zero_forward')})",f"({_repeat('b','c','0','L','trim_zero_backward')}) -> M=0"),
        ('prime_field_polynomial_trim_zero_of_empty','prime_field_polynomial_trim_empty_of_zero'),
        _intro(*PARAMETERS,'h') + ('split','intro hz')
        + _call('prime_field_polynomial_trim_zero_of_empty',*PARAMETERS) + ('exact h','exact hz','intro hz')
        + _call('prime_field_polynomial_trim_empty_of_zero',*PARAMETERS) + ('exact h','exact hz'),
        'For an actual trim, empty output and an all-zero input prefix are constructively equivalent.',
    )
    return bounded, bounds, head, zero, empty, iff


def _uniqueness_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    arguments = (*PARAMETERS,'u','f','g','N')
    other = ('p','b','c','L','u','f','g','N')
    hypotheses = (f"({_trim(*PARAMETERS,'unique_first')}) -> ({_trim(*other,'unique_second')}) -> ")
    body = _intro(*arguments,'h','hk')
    body += (f"have hbound : {_and(_le('t','L','compare_t'),_le('M','L','compare_M'))}",)
    body += _call('prime_field_polynomial_trim_length_bounds',*PARAMETERS) + ('exact h','cases hbound')
    body += (f"have horder : ({_le('t','u','compare_le')}) \\/ ({_lt('u','t','compare_lt')})",)
    body += _call('le_or_lt','t','u') + ('cases horder','exact horder_left','exfalso','have hN : N=0 \\/ ~(N=0)')
    body += _call('eq_decidable','N','0') + ('cases hN',f"have hkcopy : {_trim(*other,'compare_second_copy')}",'exact hk')
    body += _parts('hkcopy',5) + ('have hlen : L=u','trans u+N','exact hkcopy_left','rewrite hN_left','simp','rewrite hlen at hbound_left')
    body += _call('lt_not_le','u','t') + ('exact horder_right','exact hbound_left',f"have hcopy : {_trim(*PARAMETERS,'compare_first_copy')}",'exact h')
    body += _parts('hcopy',5) + (f"have hz : {_at('b','c','u','0','compare_zero')}",)
    body += _call('hcopy_right_right_left','u') + ('exact horder_right',)
    body += _call('prime_field_polynomial_trim_leading_source_nonzero',*other,'0')
    body += ('exact hk','exact hN_right','exact hz','refl')
    le = spec(
        'prime_field_polynomial_trim_removed_le',
        f"forall {' '.join(arguments)}. {hypotheses}({_le('t','u','unique_removed_le')})",
        ('prime_field_polynomial_trim_length_bounds','le_or_lt','eq_decidable','lt_not_le','prime_field_polynomial_trim_leading_source_nonzero'), body,
        'One normalized cut cannot lie after another: otherwise a supposedly leading nonzero coefficient belongs to the other removed zero prefix.',
    )
    reverse = (*other,'t','d','e','M')
    removed = spec(
        'prime_field_polynomial_trim_removed_count_unique',
        f"forall {' '.join(arguments)}. {hypotheses}t=u",
        ('le_antisymm','prime_field_polynomial_trim_removed_le'),
        _intro(*arguments,'h','hk') + _call('le_antisymm','t','u')
        + _call('prime_field_polynomial_trim_removed_le',*arguments) + ('exact h','exact hk')
        + _call('prime_field_polynomial_trim_removed_le',*reverse) + ('exact hk','exact h'),
        'The number of removed leading zero coefficients is uniquely determined by the annotated input prefix.',
    )
    body = _intro(*arguments,'h','hk') + ('have ht : t=u',)
    body += _call('prime_field_polynomial_trim_removed_count_unique',*arguments) + ('exact h','exact hk')
    body += _parts('h',5) + _parts('hk',5)
    body += _call('add_left_cancel','t','M','N') + ('trans L','symm','exact h_left','trans u+N','exact hk_left','congr','symm','exact ht','refl')
    retained = spec(
        'prime_field_polynomial_trim_retained_length_unique',
        f"forall {' '.join(arguments)}. {hypotheses}M=N",
        ('prime_field_polynomial_trim_removed_count_unique','add_left_cancel'), body,
        'The retained representation length is unique by the actual length split and additive cancellation.',
    )
    body = _intro(*arguments,'h','hk') + ('have ht : t=u',)
    body += _call('prime_field_polynomial_trim_removed_count_unique',*arguments) + ('exact h','exact hk','have hM : M=N')
    body += _call('prime_field_polynomial_trim_retained_length_unique',*arguments) + ('exact h','exact hk')
    body += _parts('h',5) + _parts('hk',5)
    body += _rewrite_all('ht',_suffix('b','c','t','d','e','M','unique_suffix_t'),'t','h_right_right_right_left')
    body += _rewrite_all('hM',_suffix('b','c','u','d','e','M','unique_suffix_M'),'M','h_right_right_right_left')
    body += _rewrite_all('hM',_equal('d','e','f','g','M','unique_output'),'M')
    body += _call('prime_field_polynomial_suffix_equal','b','c','u','d','e','f','g','N')
    body += ('exact h_right_right_right_left','exact hk_right_right_right_left')
    equal = spec(
        'prime_field_polynomial_trim_output_equal',
        f"forall {' '.join(arguments)}. {hypotheses}({_equal('d','e','f','g','M','unique_coefficients')})",
        ('prime_field_polynomial_trim_removed_count_unique','prime_field_polynomial_trim_retained_length_unique','prime_field_polynomial_suffix_equal'), body,
        'All actual trims of the same input agree coefficientwise on the unique retained prefix; no beta-code identity follows.',
    )
    chosen = ('p','b','c','L','x','x1','x2','x3')
    full = (*chosen,'u','f','g','N')
    unique = _and('t=u','M=N',_equal('d','e','f','g','M','exists_unique_values'))
    body = _intro('p','b','c','L','hc') + (f"have ht : exists t d e M. ({_trim(*PARAMETERS,'exists_unique_chosen')})",)
    body += _call('prime_field_polynomial_trim_exists','p','b','c','L')
    body += ('exact hc','cases ht','cases ht_witness','cases ht_witness_witness','cases ht_witness_witness_witness','exists x','exists x1','exists x2','exists x3','split','exact ht_witness_witness_witness_witness')
    body += _intro('u','f','g','N','hk') + ('split',)
    body += _call('prime_field_polynomial_trim_removed_count_unique',*full) + ('exact ht_witness_witness_witness_witness','exact hk','split')
    body += _call('prime_field_polynomial_trim_retained_length_unique',*full) + ('exact ht_witness_witness_witness_witness','exact hk')
    body += _call('prime_field_polynomial_trim_output_equal',*full) + ('exact ht_witness_witness_witness_witness','exact hk')
    exists = spec(
        'prime_field_polynomial_trim_exists_unique',
        f"forall p b c L. ({_coeff('p','b','c','L','unique_input')}) -> exists t d e M. "
        + _and(_trim(*PARAMETERS,'unique_constructed'),f"forall u f g N. ({_trim(*other,'unique_comparison')}) -> ({unique})"),
        ('prime_field_polynomial_trim_exists','prime_field_polynomial_trim_removed_count_unique','prime_field_polynomial_trim_retained_length_unique','prime_field_polynomial_trim_output_equal'), body,
        'Construct an actual trim and prove unique removed count, retained length and decoded coefficients against every other actual trim.',
    )
    return le, removed, retained, equal, exists


def _degree_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    body = _intro(*PARAMETERS,'q','h','hlen') + ('split','exact hlen','split')
    body += _call('prime_field_polynomial_trim_output_coefficients',*PARAMETERS) + ('exact h',)
    body += _parts('h',5) + ('cases h_right_right_right_right','exfalso','have hz : S q=0','trans M','symm','exact hlen','exact h_right_right_right_right_left')
    body += _call('succ_ne_zero','q') + ('exact hz','exact h_right_right_right_right_right')
    degree = spec(
        'prime_field_polynomial_trim_represented_degree',
        f"forall {' '.join(PARAMETERS)} q. ({_trim(*PARAMETERS,'trim_degree_input')}) -> M=S q -> "
        f"({_degree('p','d','e','M','q','trim_degree_result')})",
        ('prime_field_polynomial_trim_output_coefficients','succ_ne_zero'), body,
        'Every nonempty actual trim has the existing represented degree given by the predecessor of its retained length; the zero polynomial receives no degree.',
    )
    body = _intro(*PARAMETERS,'h','hM') + ('have hq : exists q. M=S q',)
    body += _call('nonzero_is_succ','M') + ('exact hM','cases hq','exists x')
    body += _call('prime_field_polynomial_trim_represented_degree',*PARAMETERS,'x') + ('exact h','exact hq_witness')
    nonempty = spec(
        'prime_field_polynomial_trim_nonempty_degree_exists',
        f"forall {' '.join(PARAMETERS)}. ({_trim(*PARAMETERS,'trim_nonempty_input')}) -> ~(M=0) -> "
        f"exists q. ({_degree('p','d','e','M','q','trim_nonempty_degree')})",
        ('nonzero_is_succ','prime_field_polynomial_trim_represented_degree'), body,
        'Positive retained length constructs an actual represented degree, with no claim of a degree for empty output.',
    )
    identity = spec(
        'prime_field_polynomial_trim_represented_identity',
        f"forall p b c L q. ({_degree('p','b','c','L','q','trim_already_normal')}) -> "
        f"({_trim('p','b','c','L','0','b','c','L','trim_identity')})",
        ('zero_add','beta_repeat_empty'),
        _intro('p','b','c','L','q','h') + _parts('h',3)
        + ('split','symm') + _call('zero_add','L') + ('split','exact h_right_left','split')
        + _call('beta_repeat_empty','b','c','0','0') + ('refl','split')
        + _intro('i','a','hi','ha') + ('have heq : 0+i=i',) + _call('zero_add','i')
        + ('rewrite heq at ha','rewrite heq at ha','exact ha','right','exact h_right_right'),
        'A canonical nonzero-leading representation trims to itself with zero removals, preserving its actual length and all decoded coefficients.',
    )
    return degree, nonempty, identity


def make_prime_field_polynomial_trim_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (*_suffix_rows(spec), *_construction_rows(spec), *_consequence_rows(spec),
            *_uniqueness_rows(spec), *_degree_rows(spec))


__all__ = [
    'prime_field_polynomial_suffix_relation', 'prime_field_polynomial_trim_relation',
    'make_prime_field_polynomial_trim_candidate_theorems',
]
