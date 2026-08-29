"""Canonical finite coefficient tables over the already proved prime fields.

Coefficients are highest-degree-first, as in the existing T12 Horner graph.
Length is a representation length, not a proved degree: leading zeroes and
the empty zero polynomial are allowed.  The bound and prefix-equality graphs
are exact reused finite-coding relations; beta code numbers are never unique.
All new operations describe actual decoded values, not supplied algebra laws.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_division_prefix_candidate import division_prefix
from .finite_fold_surface import _beta_at_term
from .finite_omission_candidate import _bounded_into_term
from .finite_pointwise_mul_product_candidate import _pointwise_mul_prefix_term
from .matrix_coded_product_candidate import _pointwise_add_terms
from .matrix_recursive_determinant_candidate import _prefix as _prefix_equal
from .prime_field_arithmetic_candidate import (
    _add as _field_add, _and, _call, _intro, _lt, _mul as _field_mul,
    _part, _parts, _prime, _public, _residue,
)
from .prime_field_tables_candidate import _rewrite_all


def _at(b: str, c: str, i: str, value: str, tag: str) -> str:
    return _beta_at_term(b, c, i, value, tag="pfp_" + tag, avoid=())


def _coeff(p: str, b: str, c: str, length: str, tag: str) -> str:
    return _bounded_into_term(b, c, length, p, tag="pfp_" + tag, avoid=())


def _equal(b: str, c: str, d: str, e: str, length: str, tag: str) -> str:
    return _prefix_equal(b, c, d, e, length, "pfp_" + tag)


def _repeat(b: str, c: str, a: str, length: str, tag: str) -> str:
    i = "pfp_repeat_index_" + tag
    return f"forall {i}. ({_lt(i,length,tag+'index')}) -> ({_at(b,c,i,a,tag+'entry')})"


def _normalization(p: str, b: str, c: str, d: str, e: str, length: str, tag: str) -> str:
    i, a, r = (f"pfp_{role}_{tag}" for role in ("index", "source", "residue"))
    return f"forall {i}. ({_lt(i,length,tag+'index')}) -> exists {a} {r}. " + _and(
        _at(b,c,i,a,tag+'source'), _at(d,e,i,r,tag+'target'), _residue(p,a,r,tag+'residue'),
    )


def _add(p: str, ab: str, ac: str, bb: str, bc: str, cb: str, cc: str, length: str, tag: str) -> str:
    i, a, b, value = (f"pfp_{role}_{tag}" for role in ("index", "left", "right", "value"))
    return f"forall {i}. ({_lt(i,length,tag+'index')}) -> exists {a} {b} {value}. " + _and(
        _at(ab,ac,i,a,tag+'left'), _at(bb,bc,i,b,tag+'right'), _at(cb,cc,i,value,tag+'target'),
        _field_add(p,a,b,value,tag+'operation'),
    )


def _scale(p: str, k: str, ab: str, ac: str, bb: str, bc: str, length: str, tag: str) -> str:
    i, a, value = (f"pfp_{role}_{tag}" for role in ("index", "source", "value"))
    points = f"forall {i}. ({_lt(i,length,tag+'index')}) -> exists {a} {value}. " + _and(
        _at(ab,ac,i,a,tag+'source'), _at(bb,bc,i,value,tag+'target'),
        _field_mul(p,k,a,value,tag+'operation'),
    )
    return _and(_lt(k,p,tag+'scalar'), points)


def prime_field_polynomial_coefficients_relation(p: str, b: str, c: str, length: str, *, tag: str, variables: tuple[str, ...]) -> str:
    """Exactly BoundedInto(b,c,length,p), including the empty coefficient table."""
    return _public(_coeff, (p,b,c,length), tag=tag, variables=variables)


def prime_field_polynomial_equal_relation(b: str, c: str, d: str, e: str, length: str, *, tag: str, variables: tuple[str, ...]) -> str:
    """Existing decoded-prefix preservation; not equality of raw beta codes."""
    return _public(_equal, (b,c,d,e,length), tag=tag, variables=variables)


def prime_field_polynomial_normalization_relation(p: str, b: str, c: str, d: str, e: str, length: str, *, tag: str, variables: tuple[str, ...]) -> str:
    """Each target coefficient is the actual bounded residue of its source."""
    return _public(_normalization, (p,b,c,d,e,length), tag=tag, variables=variables)


def prime_field_polynomial_add_relation(p: str, ab: str, ac: str, bb: str, bc: str, cb: str, cc: str, length: str, *, tag: str, variables: tuple[str, ...]) -> str:
    """Actual field addition at each aligned coefficient position."""
    return _public(_add, (p,ab,ac,bb,bc,cb,cc,length), tag=tag, variables=variables)


def prime_field_polynomial_scale_relation(p: str, k: str, ab: str, ac: str, bb: str, bc: str, length: str, *, tag: str, variables: tuple[str, ...]) -> str:
    """A canonical scalar and actual field products, also for length zero."""
    return _public(_scale, (p,k,ab,ac,bb,bc,length), tag=tag, variables=variables)


def _normalization_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    witness = "hpoint_witness_witness_witness"
    return (
        spec(
            "prime_field_polynomial_normalization_from_division",
            f"forall p b c qb qc rb rc l. ({division_prefix('p','b','c','qb','qc','rb','rc','l',tag='pfp_division')}) -> "
            f"({_normalization('p','b','c','rb','rc','l','division_result')})",
            ("remainder_decomposition_to_mod_eq", "mul_comm"),
            _intro("p","b","c","qb","qc","rb","rc","l","h","i","hi")
            + (f"have hpoint : exists a q r. {_and(_at('b','c','i','a','division_source'),_at('qb','qc','i','q','division_quotient'),_at('rb','rc','i','r','division_remainder'),'a=p*q+r',_lt('r','p','division_bound'))}",)
            + _call("h","i") + ("exact hi","cases hpoint","cases hpoint_witness","cases hpoint_witness_witness")
            + _parts(witness,5) + ("exists x","exists x2","split",f"exact {_part(witness,5,0)}","split",f"exact {_part(witness,5,2)}","split",f"exact {_part(witness,5,4)}")
            + _call("remainder_decomposition_to_mod_eq","p","x","x1","x2")
            + ("trans p*x1+x2",f"exact {_part(witness,5,3)}","congr") + _call("mul_comm","p","x1") + ("refl",),
            "Actual finite quotient/remainder witnesses give genuine coefficientwise canonical normalization.",
        ),
        spec(
            "prime_field_polynomial_normalization_exists",
            f"forall p b c l. ~(p=0) -> exists d e. ({_normalization('p','b','c','d','e','l','exists')})",
            ("beta_division_prefix_exists", "prime_field_polynomial_normalization_from_division"),
            _intro("p","b","c","l","hp")
            + (f"have hd : exists qb qc rb rc. ({division_prefix('p','b','c','qb','qc','rb','rc','l',tag='pfp_exists_division')})",)
            + _call("beta_division_prefix_exists","p","b","c","l") + ("exact hp","cases hd","cases hd_witness","cases hd_witness_witness","cases hd_witness_witness_witness","exists x2","exists x3")
            + _call("prime_field_polynomial_normalization_from_division","p","b","c","x","x1","x2","x3","l")
            + ("exact hd_witness_witness_witness_witness",),
            "Every natural coefficient table has an actual canonical reduction at every nonzero modulus, including empty tables.",
        ),
        spec(
            "prime_field_polynomial_normalization_entry",
            f"forall p b c d e l i a r. ({_normalization('p','b','c','d','e','l','entry_table')}) -> "
            f"({_lt('i','l','entry_index')}) -> ({_at('b','c','i','a','entry_source')}) -> ({_at('d','e','i','r','entry_target')}) -> ({_residue('p','a','r','entry_value')})",
            ("beta_at_unique",),
            _intro("p","b","c","d","e","l","i","a","r","h","hi","ha","hr")
            + (f"have hpoint : exists u v. {_and(_at('b','c','i','u','entry_chosen_source'),_at('d','e','i','v','entry_chosen_target'),_residue('p','u','v','entry_chosen_value'))}",)
            + _call("h","i") + ("exact hi","cases hpoint","cases hpoint_witness") + _parts("hpoint_witness_witness",3)
            + ("have heq : x=a",) + _call("beta_at_unique","b","c","i","x","a") + ("exact hpoint_witness_witness_left","exact ha","have hres : x1=r")
            + _call("beta_at_unique","d","e","i","x1","r") + ("exact hpoint_witness_witness_right_left","exact hr")
            + _rewrite_all("heq",_residue('p','x','x1','entry_transport'),'x',"hpoint_witness_witness_right_right")
            + _rewrite_all("hres",_residue('p','a','x1','entry_transport_result'),'x1',"hpoint_witness_witness_right_right")
            + ("exact hpoint_witness_witness_right_right",),
            "All decoded entries satisfy normalization, not just the initially chosen beta witnesses.",
        ),
        spec(
            "prime_field_polynomial_normalization_bounded",
            f"forall p b c d e l. ({_normalization('p','b','c','d','e','l','bounded_source')}) -> ({_coeff('p','d','e','l','bounded_result')})",
            (),
            _intro("p","b","c","d","e","l","h","i","hi")
            + (f"have hpoint : exists a r. {_and(_at('b','c','i','a','bounded_source_entry'),_at('d','e','i','r','bounded_target_entry'),_residue('p','a','r','bounded_residue'))}",)
            + _call("h","i") + ("exact hi","cases hpoint","cases hpoint_witness") + _parts("hpoint_witness_witness",4)
            + ("exists x1","split","exact hpoint_witness_witness_right_left","exact hpoint_witness_witness_right_right_left"),
            "The normalized table really has every coefficient strictly below the modulus.",
        ),
        spec(
            "prime_field_polynomial_normalization_functional",
            f"forall p b c d e f g l. ({_normalization('p','b','c','d','e','l','functional_first')}) -> "
            f"({_normalization('p','b','c','f','g','l','functional_second')}) -> ({_equal('d','e','f','g','l','functional_result')})",
            ("beta_at_exists", "prime_field_polynomial_normalization_entry", "binary_canonical_residue_functional"),
            _intro("p","b","c","d","e","f","g","l","hfirst","hsecond","i","r","hi","hr")
            + (f"have ha : exists a. ({_at('b','c','i','a','functional_source')})",) + _call("beta_at_exists","b","c","i") + ("cases ha",)
            + (f"have hs : exists s. ({_at('f','g','i','s','functional_target')})",) + _call("beta_at_exists","f","g","i") + ("cases hs","have heq : r=x1")
            + _call("binary_canonical_residue_functional","p","x","r","x1")
            + _call("prime_field_polynomial_normalization_entry","p","b","c","d","e","l","i","x","r")
            + ("exact hfirst","exact hi","exact ha_witness","exact hr")
            + _call("prime_field_polynomial_normalization_entry","p","b","c","f","g","l","i","x","x1")
            + ("exact hsecond","exact hi","exact ha_witness","exact hs_witness")
            + _rewrite_all("heq",_at('f','g','i','r','functional_rewrite'),'r') + ("exact hs_witness",),
            "Normalized coefficient values are unique, while their actual beta encodings may differ.",
        ),
        spec(
            "prime_field_polynomial_normalization_reflexive",
            f"forall p b c l. ({_coeff('p','b','c','l','reflexive_source')}) -> ({_normalization('p','b','c','b','c','l','reflexive_result')})",
            ("prime_field_residue_reflexive",),
            _intro("p","b","c","l","h","i","hi")
            + (f"have ha : exists a. {_and(_at('b','c','i','a','reflexive_entry'),_lt('a','p','reflexive_bound'))}",)
            + _call("h","i") + ("exact hi","cases ha","cases ha_witness","exists x","exists x","split","exact ha_witness_left","split","exact ha_witness_left")
            + _call("prime_field_residue_reflexive","p","x") + ("exact ha_witness_right",),
            "A table already consisting of canonical coefficients normalizes to itself.",
        ),
        spec(
            "prime_field_polynomial_normalization_transport",
            f"forall p b c d e B C D E l. ({_equal('b','c','B','C','l','transport_source')}) -> ({_equal('d','e','D','E','l','transport_target')}) -> "
            f"({_normalization('p','b','c','d','e','l','transport_old')}) -> ({_normalization('p','B','C','D','E','l','transport_new')})",
            (),
            _intro("p","b","c","d","e","B","C","D","E","l","hs","ht","h","i","hi")
            + (f"have hpoint : exists a r. {_and(_at('b','c','i','a','transport_chosen_source'),_at('d','e','i','r','transport_chosen_target'),_residue('p','a','r','transport_chosen_residue'))}",)
            + _call("h","i") + ("exact hi","cases hpoint","cases hpoint_witness") + _parts("hpoint_witness_witness",3)
            + ("exists x","exists x1","split") + _call("hs","i","x") + ("exact hi","exact hpoint_witness_witness_left","split")
            + _call("ht","i","x1") + ("exact hi","exact hpoint_witness_witness_right_left","exact hpoint_witness_witness_right_right"),
            "Reencoding both finite prefixes preserves every actual normalization witness.",
        ),
        spec(
            "prime_field_polynomial_normalization_idempotent",
            f"forall p b c d e f g l. ({_normalization('p','b','c','d','e','l','idempotent_first')}) -> "
            f"({_normalization('p','d','e','f','g','l','idempotent_second')}) -> ({_equal('d','e','f','g','l','idempotent_result')})",
            ("prime_field_polynomial_normalization_functional", "prime_field_polynomial_normalization_reflexive", "prime_field_polynomial_normalization_bounded"),
            _intro("p","b","c","d","e","f","g","l","hfirst","hsecond")
            + _call("prime_field_polynomial_normalization_functional","p","d","e","d","e","f","g","l")
            + _call("prime_field_polynomial_normalization_reflexive","p","d","e","l")
            + _call("prime_field_polynomial_normalization_bounded","p","b","c","d","e","l")
            + ("exact hfirst","exact hsecond"),
            "Reducing a normalized polynomial again leaves every coefficient unchanged, not necessarily its raw code.",
        ),
    )


def _constant_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "prime_field_polynomial_repeat_coefficients",
            f"forall p b c a l. ({_lt('a','p','constant_bound')}) -> ({_repeat('b','c','a','l','constant_repeat')}) -> ({_coeff('p','b','c','l','constant_result')})",
            (),
            _intro("p","b","c","a","l","ha","hr","i","hi") + ("exists a","split")
            + _call("hr","i") + ("exact hi","exact ha"),
            "A genuinely repeated canonical value forms a bounded coefficient table, including length zero.",
        ),
        spec(
            "prime_field_polynomial_repeat_exists",
            f"forall p a l. ({_lt('a','p','repeat_domain')}) -> exists b c. {_and(_coeff('p','b','c','l','repeat_table'),_repeat('b','c','a','l','repeat_value'))}",
            ("beta_repeat_exists", "prime_field_polynomial_repeat_coefficients"),
            _intro("p","a","l","ha") + (f"have hr : exists b c. ({_repeat('b','c','a','l','repeat_chosen')})",)
            + _call("beta_repeat_exists","a","l") + ("cases hr","cases hr_witness","exists x","exists x1","split")
            + _call("prime_field_polynomial_repeat_coefficients","p","x","x1","a","l") + ("exact ha","exact hr_witness_witness","exact hr_witness_witness"),
            "Construct a finite coefficient table containing exactly the chosen canonical coefficient at every position.",
        ),
        spec(
            "prime_field_polynomial_zero_exists",
            f"forall p l. ({_prime('p','zero_domain')}) -> exists b c. {_and(_coeff('p','b','c','l','zero_table'),_repeat('b','c','0','l','zero_value'))}",
            ("prime_field_polynomial_repeat_exists", "prime_field_zero_below_prime"),
            _intro("p","l","hp") + _call("prime_field_polynomial_repeat_exists","p","0","l")
            + _call("prime_field_zero_below_prime","p") + ("exact hp",),
            "Every prime admits an actual all-zero coefficient table of every finite representation length.",
        ),
    )


def _add_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    raw = lambda a,b,c,d,e,f,l,t: _pointwise_add_terms(a,b,c,d,e,f,l,tag='pfp_'+t)
    entry_body = _intro('p','ab','ac','bb','bc','cb','cc','l','i','a','b','r','h','hi','ha','hb','hr')
    entry_body += (f"have hv : exists u v w. {_and(_at('ab','ac','i','u','add_entry_left'),_at('bb','bc','i','v','add_entry_right'),_at('cb','cc','i','w','add_entry_target'),_field_add('p','u','v','w','add_entry_operation'))}",)
    entry_body += _call('h','i') + ('exact hi','cases hv','cases hv_witness','cases hv_witness_witness') + _parts('hv_witness_witness_witness',4)
    current = ['x','x1','x2']
    for index, (b,c,value,hyp) in enumerate((('ab','ac','a','ha'),('bb','bc','b','hb'),('cb','cc','r','hr'))):
        eq = 'heq' + str(index)
        entry_body += (f'have {eq} : {current[index]}={value}',) + _call('beta_at_unique',b,c,'i',current[index],value)
        entry_body += (f'exact {_part("hv_witness_witness_witness",4,index)}',f'exact {hyp}')
        entry_body += _rewrite_all(eq,_field_add('p',*current,'add_entry_rewrite'+str(index)),current[index],'hv_witness_witness_witness_right_right_right')
        current[index] = value
    entry_body += ('exact hv_witness_witness_witness_right_right_right',)
    bounded_body = _intro('p','ab','ac','bb','bc','cb','cc','l','h')
    for index in range(3):
        if index < 2:
            bounded_body += ('split',)
        bounded_body += _intro('i','hi')
        bounded_body += (f"have hv : exists a b r. {_and(_at('ab','ac','i','a','add_bound_left'),_at('bb','bc','i','b','add_bound_right'),_at('cb','cc','i','r','add_bound_target'),_field_add('p','a','b','r','add_bound_operation'))}",)
        bounded_body += _call('h','i') + ('exact hi','cases hv','cases hv_witness','cases hv_witness_witness') + _parts('hv_witness_witness_witness',4)
        bounded_body += _parts('hv_witness_witness_witness_right_right_right',4)
        bounded_body += ('exists '+('x','x1','x2')[index],'split',f'exact {_part("hv_witness_witness_witness",4,index)}',f'exact {_part("hv_witness_witness_witness_right_right_right",4,index)}')
    return (
        spec(
            'prime_field_polynomial_add_from_normalization',
            f"forall p ab ac bb bc rb rc cb cc l. ({_coeff('p','ab','ac','l','add_source_a')}) -> ({_coeff('p','bb','bc','l','add_source_b')}) -> "
            f"({raw('ab','ac','bb','bc','rb','rc','l','add_raw')}) -> ({_normalization('p','rb','rc','cb','cc','l','add_normalize')}) -> ({_add('p','ab','ac','bb','bc','cb','cc','l','add_result')})",
            ('prime_field_residue_input_equal',),
            _intro('p','ab','ac','bb','bc','rb','rc','cb','cc','l','ha','hb','hs','hn','i','hi')
            + (f"have hva : exists a. {_and(_at('ab','ac','i','a','add_chosen_a'),_lt('a','p','add_chosen_a_bound'))}",)
            + _call('ha','i') + ('exact hi','cases hva','cases hva_witness')
            + (f"have hvb : exists b. {_and(_at('bb','bc','i','b','add_chosen_b'),_lt('b','p','add_chosen_b_bound'))}",)
            + _call('hb','i') + ('exact hi','cases hvb','cases hvb_witness')
            + (f"have hvn : exists s r. {_and(_at('rb','rc','i','s','add_chosen_sum'),_at('cb','cc','i','r','add_chosen_residue'),_residue('p','s','r','add_chosen_reduction'))}",)
            + _call('hn','i') + ('exact hi','cases hvn','cases hvn_witness') + _parts('hvn_witness_witness',3)
            + ('exists x','exists x1','exists x3','split','exact hva_witness_left','split','exact hvb_witness_left','split','exact hvn_witness_witness_right_left','split','exact hva_witness_right','split','exact hvb_witness_right')
            + _call('prime_field_residue_input_equal','p','x+x1','x2','x3') + ('symm',)
            + _call('hs','i','x','x1','x2') + ('exact hi','exact hva_witness_left','exact hvb_witness_left','exact hvn_witness_witness_left','exact hvn_witness_witness_right_right'),
            'Normalize a genuine natural pointwise sum to obtain actual canonical field sums at every coefficient.',
        ),
        spec(
            'prime_field_polynomial_add_exists',
            f"forall p ab ac bb bc l. ~(p=0) -> ({_coeff('p','ab','ac','l','add_exists_a')}) -> ({_coeff('p','bb','bc','l','add_exists_b')}) -> exists cb cc. ({_add('p','ab','ac','bb','bc','cb','cc','l','add_exists_result')})",
            ('beta_pointwise_add_prefix_exists','prime_field_polynomial_normalization_exists','prime_field_polynomial_add_from_normalization'),
            _intro('p','ab','ac','bb','bc','l','hp','ha','hb')
            + (f"have hs : exists rb rc. ({raw('ab','ac','bb','bc','rb','rc','l','add_exists_raw')})",)
            + _call('beta_pointwise_add_prefix_exists','ab','ac','bb','bc','l') + ('cases hs','cases hs_witness')
            + (f"have hn : exists cb cc. ({_normalization('p','x','x1','cb','cc','l','add_exists_normalization')})",)
            + _call('prime_field_polynomial_normalization_exists','p','x','x1','l') + ('exact hp','cases hn','cases hn_witness','exists x2','exists x3')
            + _call('prime_field_polynomial_add_from_normalization','p','ab','ac','bb','bc','x','x1','x2','x3','l')
            + ('exact ha','exact hb','exact hs_witness_witness','exact hn_witness_witness'),
            'Construct the actual finite canonical coefficient sum, without supplying a table or an addition-law premise.',
        ),
        spec(
            'prime_field_polynomial_add_entry',
            f"forall p ab ac bb bc cb cc l i a b r. ({_add('p','ab','ac','bb','bc','cb','cc','l','add_entry_table')}) -> ({_lt('i','l','add_entry_index')}) -> "
            f"({_at('ab','ac','i','a','add_entry_input_a')}) -> ({_at('bb','bc','i','b','add_entry_input_b')}) -> ({_at('cb','cc','i','r','add_entry_output')}) -> ({_field_add('p','a','b','r','add_entry_value')})",
            ('beta_at_unique',), entry_body,
            'Every decoded coefficient triple obeys the actual field-addition graph, independently of witness choices.',
        ),
        spec(
            'prime_field_polynomial_add_bounded',
            f"forall p ab ac bb bc cb cc l. ({_add('p','ab','ac','bb','bc','cb','cc','l','add_bounded_table')}) -> "
            + _and(*(_coeff('p',b,c,'l','add_bounded_'+b) for b,c in (('ab','ac'),('bb','bc'),('cb','cc')))),
            (), bounded_body,
            'All three prefixes in an actual polynomial addition consist of canonical coefficients.',
        ),
        spec(
            'prime_field_polynomial_add_functional',
            f"forall p ab ac bb bc cb cc db dc l. ({_add('p','ab','ac','bb','bc','cb','cc','l','add_functional_first')}) -> ({_add('p','ab','ac','bb','bc','db','dc','l','add_functional_second')}) -> ({_equal('cb','cc','db','dc','l','add_functional_result')})",
            ('beta_at_exists','prime_field_polynomial_add_entry','prime_field_add_functional'),
            _intro('p','ab','ac','bb','bc','cb','cc','db','dc','l','hc','hd','i','r','hi','hr')
            + (f"have ha : exists a. ({_at('ab','ac','i','a','add_functional_a')})",) + _call('beta_at_exists','ab','ac','i') + ('cases ha',)
            + (f"have hb : exists b. ({_at('bb','bc','i','b','add_functional_b')})",) + _call('beta_at_exists','bb','bc','i') + ('cases hb',)
            + (f"have hs : exists s. ({_at('db','dc','i','s','add_functional_s')})",) + _call('beta_at_exists','db','dc','i') + ('cases hs','have heq : r=x2')
            + _call('prime_field_add_functional','p','x','x1','r','x2')
            + _call('prime_field_polynomial_add_entry','p','ab','ac','bb','bc','cb','cc','l','i','x','x1','r')
            + ('exact hc','exact hi','exact ha_witness','exact hb_witness','exact hr')
            + _call('prime_field_polynomial_add_entry','p','ab','ac','bb','bc','db','dc','l','i','x','x1','x2')
            + ('exact hd','exact hi','exact ha_witness','exact hb_witness','exact hs_witness')
            + _rewrite_all('heq',_at('db','dc','i','r','add_functional_rewrite'),'r') + ('exact hs_witness',),
            'The sum is unique as a coefficient prefix; arbitrary beta recodings remain admissible.',
        ),
        spec(
            'prime_field_polynomial_add_transport',
            f"forall p ab ac bb bc cb cc AB AC BB BC CB CC l. ({_equal('ab','ac','AB','AC','l','add_transport_a')}) -> ({_equal('bb','bc','BB','BC','l','add_transport_b')}) -> ({_equal('cb','cc','CB','CC','l','add_transport_c')}) -> "
            f"({_add('p','ab','ac','bb','bc','cb','cc','l','add_transport_old')}) -> ({_add('p','AB','AC','BB','BC','CB','CC','l','add_transport_new')})",
            (),
            _intro('p','ab','ac','bb','bc','cb','cc','AB','AC','BB','BC','CB','CC','l','ha','hb','hc','h','i','hi')
            + (f"have hv : exists a b r. {_and(_at('ab','ac','i','a','add_transport_chosen_a'),_at('bb','bc','i','b','add_transport_chosen_b'),_at('cb','cc','i','r','add_transport_chosen_r'),_field_add('p','a','b','r','add_transport_operation'))}",)
            + _call('h','i') + ('exact hi','cases hv','cases hv_witness','cases hv_witness_witness') + _parts('hv_witness_witness_witness',4)
            + ('exists x','exists x1','exists x2','split') + _call('ha','i','x') + ('exact hi','exact hv_witness_witness_witness_left','split')
            + _call('hb','i','x1') + ('exact hi','exact hv_witness_witness_witness_right_left','split')
            + _call('hc','i','x2') + ('exact hi','exact hv_witness_witness_witness_right_right_left','exact hv_witness_witness_witness_right_right_right'),
            'Independent beta recoding of both inputs and the output preserves actual coefficient addition.',
        ),
        spec(
            'prime_field_polynomial_add_commutative',
            f"forall p ab ac bb bc cb cc l. ({_add('p','ab','ac','bb','bc','cb','cc','l','add_comm_old')}) -> ({_add('p','bb','bc','ab','ac','cb','cc','l','add_comm_new')})",
            ('prime_field_add_commutative',),
            _intro('p','ab','ac','bb','bc','cb','cc','l','h','i','hi')
            + (f"have hv : exists a b r. {_and(_at('ab','ac','i','a','add_comm_chosen_a'),_at('bb','bc','i','b','add_comm_chosen_b'),_at('cb','cc','i','r','add_comm_chosen_r'),_field_add('p','a','b','r','add_comm_operation'))}",)
            + _call('h','i') + ('exact hi','cases hv','cases hv_witness','cases hv_witness_witness') + _parts('hv_witness_witness_witness',4)
            + ('exists x1','exists x','exists x2','split','exact hv_witness_witness_witness_right_left','split','exact hv_witness_witness_witness_left','split','exact hv_witness_witness_witness_right_right_left')
            + _call('prime_field_add_commutative','p','x','x1','x2') + ('exact hv_witness_witness_witness_right_right_right',),
            'Coefficient addition commutes for actual finite tables, including the empty table.',
        ),
        spec(
            'prime_field_polynomial_add_zero_right',
            f"forall p b c zb zc l. ({_prime('p','add_zero_prime')}) -> ({_coeff('p','b','c','l','add_zero_coefficients')}) -> ({_repeat('zb','zc','0','l','add_zero_table')}) -> ({_add('p','b','c','zb','zc','b','c','l','add_zero_result')})",
            ('prime_field_add_zero_right',),
            _intro('p','b','c','zb','zc','l','hp','hc','hz','i','hi')
            + (f"have ha : exists a. {_and(_at('b','c','i','a','add_zero_chosen'),_lt('a','p','add_zero_bound'))}",)
            + _call('hc','i') + ('exact hi','cases ha','cases ha_witness','exists x','exists 0','exists x','split','exact ha_witness_left','split')
            + _call('hz','i') + ('exact hi','split','exact ha_witness_left') + _call('prime_field_add_zero_right','p','x') + ('exact hp','exact ha_witness_right'),
            'An actual all-zero table is an additive identity at every finite representation length.',
        ),
    )


def _scale_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    raw = lambda a,b,c,d,e,f,l,t: _pointwise_mul_prefix_term(a,b,c,d,e,f,l,tag='pfp_'+t,variables=(a,b,c,d,e,f,l))
    entry_body = _intro('p','k','ab','ac','bb','bc','l','i','a','r','h','hi','ha','hr') + ('cases h',)
    entry_body += (f"have hv : exists u v. {_and(_at('ab','ac','i','u','scale_entry_source'),_at('bb','bc','i','v','scale_entry_target'),_field_mul('p','k','u','v','scale_entry_operation'))}",)
    entry_body += _call('h_right','i') + ('exact hi','cases hv','cases hv_witness') + _parts('hv_witness_witness',3)
    current = ['x','x1']
    for index, (b,c,value,hyp) in enumerate((('ab','ac','a','ha'),('bb','bc','r','hr'))):
        eq = 'heq' + str(index)
        entry_body += (f'have {eq} : {current[index]}={value}',) + _call('beta_at_unique',b,c,'i',current[index],value)
        entry_body += (f'exact {_part("hv_witness_witness",3,index)}',f'exact {hyp}')
        entry_body += _rewrite_all(eq,_field_mul('p','k',*current,'scale_entry_rewrite'+str(index)),current[index],'hv_witness_witness_right_right')
        current[index] = value
    entry_body += ('exact hv_witness_witness_right_right',)
    bounded_body = _intro('p','k','ab','ac','bb','bc','l','h') + ('cases h','split')
    for index in range(2):
        bounded_body += _intro('i','hi')
        bounded_body += (f"have hv : exists a r. {_and(_at('ab','ac','i','a','scale_bound_source'),_at('bb','bc','i','r','scale_bound_target'),_field_mul('p','k','a','r','scale_bound_operation'))}",)
        bounded_body += _call('h_right','i') + ('exact hi','cases hv','cases hv_witness') + _parts('hv_witness_witness',3)
        bounded_body += _parts('hv_witness_witness_right_right',4)
        bounded_body += ('exists '+('x','x1')[index],'split',f'exact {_part("hv_witness_witness",3,index)}',f'exact {_part("hv_witness_witness_right_right",4,index+1)}')
    return (
        spec(
            'prime_field_polynomial_scale_from_normalization',
            f"forall p k kb kc ab ac rb rc bb bc l. ({_lt('k','p','scale_scalar')}) -> ({_coeff('p','ab','ac','l','scale_source')}) -> ({_repeat('kb','kc','k','l','scale_repeated')}) -> "
            f"({raw('kb','kc','ab','ac','rb','rc','l','scale_raw')}) -> ({_normalization('p','rb','rc','bb','bc','l','scale_normalize')}) -> ({_scale('p','k','ab','ac','bb','bc','l','scale_result')})",
            ('prime_field_residue_input_equal',),
            _intro('p','k','kb','kc','ab','ac','rb','rc','bb','bc','l','hk','hc','hr','hm','hn') + ('split','exact hk') + _intro('i','hi')
            + (f"have ha : exists a. {_and(_at('ab','ac','i','a','scale_chosen_a'),_lt('a','p','scale_chosen_bound'))}",)
            + _call('hc','i') + ('exact hi','cases ha','cases ha_witness')
            + (f"have hvn : exists n r. {_and(_at('rb','rc','i','n','scale_chosen_product'),_at('bb','bc','i','r','scale_chosen_output'),_residue('p','n','r','scale_chosen_residue'))}",)
            + _call('hn','i') + ('exact hi','cases hvn','cases hvn_witness') + _parts('hvn_witness_witness',3)
            + ('exists x','exists x2','split','exact ha_witness_left','split','exact hvn_witness_witness_right_left','split','exact hk','split','exact ha_witness_right')
            + _call('prime_field_residue_input_equal','p','k*x','x1','x2') + ('symm',) + _call('hm','i','k','x','x1')
            + ('exact hi',) + _call('hr','i') + ('exact hi','exact ha_witness_left','exact hvn_witness_witness_left','exact hvn_witness_witness_right_right'),
            'Normalize an actual pointwise product with a repeated scalar to obtain genuine canonical scalar multiplication.',
        ),
        spec(
            'prime_field_polynomial_scale_exists',
            f"forall p k ab ac l. ~(p=0) -> ({_lt('k','p','scale_exists_scalar')}) -> ({_coeff('p','ab','ac','l','scale_exists_source')}) -> exists bb bc. ({_scale('p','k','ab','ac','bb','bc','l','scale_exists_result')})",
            ('beta_repeat_exists','beta_pointwise_mul_prefix_exists','prime_field_polynomial_normalization_exists','prime_field_polynomial_scale_from_normalization'),
            _intro('p','k','ab','ac','l','hp','hk','hc')
            + (f"have hr : exists kb kc. ({_repeat('kb','kc','k','l','scale_exists_repeat')})",) + _call('beta_repeat_exists','k','l') + ('cases hr','cases hr_witness')
            + (f"have hm : exists rb rc. ({raw('x','x1','ab','ac','rb','rc','l','scale_exists_raw')})",)
            + _call('beta_pointwise_mul_prefix_exists','x','x1','ab','ac','l') + ('cases hm','cases hm_witness')
            + (f"have hn : exists bb bc. ({_normalization('p','x2','x3','bb','bc','l','scale_exists_normalization')})",)
            + _call('prime_field_polynomial_normalization_exists','p','x2','x3','l') + ('exact hp','cases hn','cases hn_witness','exists x4','exists x5')
            + _call('prime_field_polynomial_scale_from_normalization','p','k','x','x1','ab','ac','x2','x3','x4','x5','l')
            + ('exact hk','exact hc','exact hr_witness_witness','exact hm_witness_witness','exact hn_witness_witness'),
            'Every canonical scalar has an actual finite coefficient-product table, including scalar zero and empty inputs.',
        ),
        spec(
            'prime_field_polynomial_scale_entry',
            f"forall p k ab ac bb bc l i a r. ({_scale('p','k','ab','ac','bb','bc','l','scale_entry_table')}) -> ({_lt('i','l','scale_entry_index')}) -> ({_at('ab','ac','i','a','scale_entry_input')}) -> ({_at('bb','bc','i','r','scale_entry_output')}) -> ({_field_mul('p','k','a','r','scale_entry_value')})",
            ('beta_at_unique',), entry_body,
            'Every decoded input/output pair of the scalar table satisfies actual canonical multiplication.',
        ),
        spec(
            'prime_field_polynomial_scale_bounded',
            f"forall p k ab ac bb bc l. ({_scale('p','k','ab','ac','bb','bc','l','scale_bounded_operation')}) -> " + _and(_coeff('p','ab','ac','l','scale_bounded_source'),_coeff('p','bb','bc','l','scale_bounded_target')),
            (), bounded_body,
            'Both the input and the constructed output of scalar multiplication have bounded coefficients.',
        ),
        spec(
            'prime_field_polynomial_scale_functional',
            f"forall p k ab ac bb bc cb cc l. ({_scale('p','k','ab','ac','bb','bc','l','scale_functional_first')}) -> ({_scale('p','k','ab','ac','cb','cc','l','scale_functional_second')}) -> ({_equal('bb','bc','cb','cc','l','scale_functional_result')})",
            ('beta_at_exists','prime_field_polynomial_scale_entry','prime_field_multiply_functional'),
            _intro('p','k','ab','ac','bb','bc','cb','cc','l','hb','hc','i','r','hi','hr')
            + (f"have ha : exists a. ({_at('ab','ac','i','a','scale_functional_a')})",) + _call('beta_at_exists','ab','ac','i') + ('cases ha',)
            + (f"have hs : exists s. ({_at('cb','cc','i','s','scale_functional_s')})",) + _call('beta_at_exists','cb','cc','i') + ('cases hs','have heq : r=x1')
            + _call('prime_field_multiply_functional','p','k','x','r','x1')
            + _call('prime_field_polynomial_scale_entry','p','k','ab','ac','bb','bc','l','i','x','r') + ('exact hb','exact hi','exact ha_witness','exact hr')
            + _call('prime_field_polynomial_scale_entry','p','k','ab','ac','cb','cc','l','i','x','x1') + ('exact hc','exact hi','exact ha_witness','exact hs_witness')
            + _rewrite_all('heq',_at('cb','cc','i','r','scale_functional_rewrite'),'r') + ('exact hs_witness',),
            'The scalar product has a unique decoded coefficient prefix, not a unique raw beta code.',
        ),
        spec(
            'prime_field_polynomial_scale_transport',
            f"forall p k ab ac bb bc AB AC BB BC l. ({_equal('ab','ac','AB','AC','l','scale_transport_source')}) -> ({_equal('bb','bc','BB','BC','l','scale_transport_target')}) -> ({_scale('p','k','ab','ac','bb','bc','l','scale_transport_old')}) -> ({_scale('p','k','AB','AC','BB','BC','l','scale_transport_new')})",
            (),
            _intro('p','k','ab','ac','bb','bc','AB','AC','BB','BC','l','ha','hb','h') + ('cases h','split','exact h_left') + _intro('i','hi')
            + (f"have hv : exists a r. {_and(_at('ab','ac','i','a','scale_transport_a'),_at('bb','bc','i','r','scale_transport_r'),_field_mul('p','k','a','r','scale_transport_operation'))}",)
            + _call('h_right','i') + ('exact hi','cases hv','cases hv_witness') + _parts('hv_witness_witness',3)
            + ('exists x','exists x1','split') + _call('ha','i','x') + ('exact hi','exact hv_witness_witness_left','split')
            + _call('hb','i','x1') + ('exact hi','exact hv_witness_witness_right_left','exact hv_witness_witness_right_right'),
            'Independent recoding of the source and target preserves actual scalar multiplication.',
        ),
        spec(
            'prime_field_polynomial_scale_one',
            f"forall p b c l. ({_prime('p','scale_one_prime')}) -> ({_coeff('p','b','c','l','scale_one_coefficients')}) -> ({_scale('p','1','b','c','b','c','l','scale_one_result')})",
            ('prime_two_le','prime_field_multiply_one_left'),
            _intro('p','b','c','l','hp','hc') + ('split',) + _call('prime_two_le','p') + ('exact hp',) + _intro('i','hi')
            + (f"have ha : exists a. {_and(_at('b','c','i','a','scale_one_chosen'),_lt('a','p','scale_one_bound'))}",)
            + _call('hc','i') + ('exact hi','cases ha','cases ha_witness','exists x','exists x','split','exact ha_witness_left','split','exact ha_witness_left')
            + _call('prime_field_multiply_one_left','p','x') + ('exact hp','exact ha_witness_right'),
            'The actual canonical scalar one acts identically on every finite coefficient prefix.',
        ),
        spec(
            'prime_field_polynomial_scale_zero',
            f"forall p b c zb zc l. ({_prime('p','scale_zero_prime')}) -> ({_coeff('p','b','c','l','scale_zero_coefficients')}) -> ({_repeat('zb','zc','0','l','scale_zero_table')}) -> ({_scale('p','0','b','c','zb','zc','l','scale_zero_result')})",
            ('prime_field_zero_below_prime','prime_field_multiply_zero_left'),
            _intro('p','b','c','zb','zc','l','hp','hc','hz') + ('split',) + _call('prime_field_zero_below_prime','p') + ('exact hp',) + _intro('i','hi')
            + (f"have ha : exists a. {_and(_at('b','c','i','a','scale_zero_chosen'),_lt('a','p','scale_zero_bound'))}",)
            + _call('hc','i') + ('exact hi','cases ha','cases ha_witness','exists x','exists 0','split','exact ha_witness_left','split')
            + _call('hz','i') + ('exact hi',) + _call('prime_field_multiply_zero_left','p','x') + ('exact hp','exact ha_witness_right'),
            'Scalar zero produces a genuinely encoded zero polynomial, not merely a zero output claim.',
        ),
    )


def _algebra_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """Lift already proved scalar laws by actual beta lookups, not axioms."""
    def choices(keys: tuple[str, ...], tag: str):
        body: tuple[str, ...] = ()
        values = {'u': ('r','hr')}
        for index, key in enumerate(keys):
            name = 'x' + (str(index) if index else '')
            hyp = 'entry_' + key
            body += (f"have {hyp} : exists z. ({_at(key+'b',key+'c','i','z',tag+key)})",)
            body += _call('beta_at_exists',key+'b',key+'c','i') + ('cases '+hyp,)
            values[key] = name, hyp+'_witness'
        return body, values

    def addition(values, a: str, b: str, c: str, hypothesis: str):
        return _call('prime_field_polynomial_add_entry','p',a+'b',a+'c',b+'b',b+'c',c+'b',c+'c','l','i',values[a][0],values[b][0],values[c][0]) + (
            'exact '+hypothesis,'exact hi','exact '+values[a][1],'exact '+values[b][1],'exact '+values[c][1],
        )

    def scale(values, k: str, a: str, b: str, hypothesis: str):
        return _call('prime_field_polynomial_scale_entry','p',k,a+'b',a+'c',b+'b',b+'c','l','i',values[a][0],values[b][0]) + (
            'exact '+hypothesis,'exact hi','exact '+values[a][1],'exact '+values[b][1],
        )

    def finish(values, tag: str):
        return _rewrite_all('heq',_at('vb','vc','i','r',tag),'r') + ('exact '+values['v'][1],)

    params = ('p','ab','ac','bb','bc','cb','cc','xb','xc','yb','yc','ub','uc','vb','vc','l')
    relations = (_add('p','ab','ac','bb','bc','xb','xc','l','assoc_ab'),_add('p','xb','xc','cb','cc','ub','uc','l','assoc_left'),_add('p','bb','bc','cb','cc','yb','yc','l','assoc_bc'),_add('p','ab','ac','yb','yc','vb','vc','l','assoc_right'))
    body = _intro(*params,'hab','hleft','hbc','hright','i','r','hi','hr')
    picked, values = choices(('a','b','c','x','y','v'),'assoc_choice')
    body += picked + (f"have heq : r={values['v'][0]}",)
    body += _call('prime_field_add_associative','p',values['a'][0],values['b'][0],values['c'][0],values['x'][0],values['y'][0],'r',values['v'][0])
    body += addition(values,'a','b','x','hab') + addition(values,'x','c','u','hleft') + addition(values,'b','c','y','hbc') + addition(values,'a','y','v','hright') + finish(values,'assoc_finish')
    associative = spec(
        'prime_field_polynomial_add_associative',
        'forall '+' '.join(params)+'. '+' -> '.join(f'({r})' for r in relations)+f" -> ({_equal('ub','uc','vb','vc','l','assoc_result')})",
        ('beta_at_exists','prime_field_add_associative','prime_field_polynomial_add_entry'), body,
        'Both actual bracketings of three finite coefficient additions yield extensionally equal prefixes.',
    )
    params = ('p','a','b','k','ab','ac','bb','bc','ub','uc','vb','vc','l')
    relations = (_field_mul('p','a','b','k','scale_assoc_scalars'),_scale('p','b','ab','ac','bb','bc','l','scale_assoc_first'),_scale('p','a','bb','bc','ub','uc','l','scale_assoc_second'),_scale('p','k','ab','ac','vb','vc','l','scale_assoc_product'))
    body = _intro(*params,'hk','hfirst','hsecond','hproduct','i','r','hi','hr')
    picked, values = choices(('a','b','v'),'scale_assoc_choice')
    body += picked + (f"have heq : r={values['v'][0]}",'symm')
    body += _call('prime_field_multiply_associative','p','a','b',values['a'][0],'k',values['b'][0],values['v'][0],'r')
    body += ('exact hk',) + scale(values,'k','a','v','hproduct') + scale(values,'b','a','b','hfirst') + scale(values,'a','b','u','hsecond') + finish(values,'scale_assoc_finish')
    scalar_associative = spec(
        'prime_field_polynomial_scale_associative',
        'forall '+' '.join(params)+'. '+' -> '.join(f'({r})' for r in relations)+f" -> ({_equal('ub','uc','vb','vc','l','scale_assoc_result')})",
        ('beta_at_exists','prime_field_multiply_associative','prime_field_polynomial_scale_entry'), body,
        'Two successive canonical scalar actions agree coefficientwise with the actual canonical product scalar.',
    )
    params = ('p','k','ab','ac','bb','bc','sb','sc','xb','xc','yb','yc','ub','uc','vb','vc','l')
    relations = (_add('p','ab','ac','bb','bc','sb','sc','l','distribute_sum'),_scale('p','k','sb','sc','ub','uc','l','distribute_left'),_scale('p','k','ab','ac','xb','xc','l','distribute_a'),_scale('p','k','bb','bc','yb','yc','l','distribute_b'),_add('p','xb','xc','yb','yc','vb','vc','l','distribute_right'))
    body = _intro(*params,'hsum','hleft','hfirst','hsecond','hright','i','r','hi','hr')
    picked, values = choices(('a','b','s','x','y','v'),'distribute_choice')
    body += picked + (f"have heq : r={values['v'][0]}",)
    body += _call('prime_field_left_distributive','p','k',values['a'][0],values['b'][0],values['s'][0],values['x'][0],values['y'][0],'r',values['v'][0])
    body += addition(values,'a','b','s','hsum') + scale(values,'k','s','u','hleft') + scale(values,'k','a','x','hfirst') + scale(values,'k','b','y','hsecond') + addition(values,'x','y','v','hright') + finish(values,'distribute_finish')
    distribute = spec(
        'prime_field_polynomial_scale_distributes_over_add',
        'forall '+' '.join(params)+'. '+' -> '.join(f'({r})' for r in relations)+f" -> ({_equal('ub','uc','vb','vc','l','distribute_result')})",
        ('beta_at_exists','prime_field_left_distributive','prime_field_polynomial_add_entry','prime_field_polynomial_scale_entry'), body,
        'Actual scalar multiplication distributes over actual coefficient addition, with code-independent output equality.',
    )
    params = ('p','a','b','k','ab','ac','xb','xc','yb','yc','ub','uc','vb','vc','l')
    relations = (_field_add('p','a','b','k','scalar_distribute_sum'),_scale('p','k','ab','ac','ub','uc','l','scalar_distribute_left'),_scale('p','a','ab','ac','xb','xc','l','scalar_distribute_a'),_scale('p','b','ab','ac','yb','yc','l','scalar_distribute_b'),_add('p','xb','xc','yb','yc','vb','vc','l','scalar_distribute_right'))
    body = _intro(*params,'hsum','hleft','hfirst','hsecond','hright','i','r','hi','hr')
    picked, values = choices(('a','x','y','v'),'scalar_distribute_choice')
    body += picked + (f"have heq : r={values['v'][0]}",)
    body += _call('prime_field_right_distributive','p',values['a'][0],'a','b','k',values['x'][0],values['y'][0],'r',values['v'][0])
    body += ('exact hsum',) + scale(values,'k','a','u','hleft') + scale(values,'a','a','x','hfirst') + scale(values,'b','a','y','hsecond') + addition(values,'x','y','v','hright') + finish(values,'scalar_distribute_finish')
    scalar_distribute = spec(
        'prime_field_polynomial_scalar_add_distributes',
        'forall '+' '.join(params)+'. '+' -> '.join(f'({r})' for r in relations)+f" -> ({_equal('ub','uc','vb','vc','l','scalar_distribute_result')})",
        ('beta_at_exists','prime_field_right_distributive','prime_field_polynomial_scale_entry','prime_field_polynomial_add_entry'), body,
        'Acting by an actual sum of scalars agrees with adding their separately constructed coefficient actions.',
    )
    return associative, scalar_associative, distribute, scalar_distribute


def make_prime_field_polynomial_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (*_normalization_rows(spec), *_constant_rows(spec), *_add_rows(spec), *_scale_rows(spec), *_algebra_rows(spec))


__all__ = [
    "prime_field_polynomial_coefficients_relation", "prime_field_polynomial_equal_relation",
    "prime_field_polynomial_normalization_relation", "prime_field_polynomial_add_relation",
    "prime_field_polynomial_scale_relation", "make_prime_field_polynomial_candidate_theorems",
]
