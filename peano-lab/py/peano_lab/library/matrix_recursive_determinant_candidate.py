"""Actual arbitrary-dimensional signed cofactor evaluation in first-order HA.

An evaluation history is a finite beta-coded DAG.  Every node is an actual
signed matrix, its dimension, and its two subtraction-free determinant
components.  A nonempty node refers only to strictly earlier nodes, one for
every genuine first-row minor, and uses their values in the checked signed
alternating fold.  In particular, arbitrary supplied numbers are never
treated as already evaluated determinants.

These formula builders and tactic scripts are untrusted authoring material.
Admission requires a separately closed original-kernel dependency bundle.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from .finite_fold_surface import _beta_at_term, _identifier, _variables
from .matrix_cofactor_expansion_candidate import _fold_terms, _pack_four, _pair
from .matrix_determinant_minors_candidate import _signed_minor_terms


class MatrixRecursiveDeterminantError(ValueError):
    """A conservative determinant surface would be malformed or capture names."""


def _safe(tag: str) -> str:
    try:
        return _identifier(tag, "recursive-determinant binder tag")
    except ValueError as error:
        raise MatrixRecursiveDeterminantError(str(error)) from error


def _arguments(*values: str) -> tuple[str, ...]:
    try:
        result = _variables(*((value, "recursive-determinant argument") for value in values))
        if len(set(result)) != len(result):
            raise ValueError("recursive-determinant arguments must be distinct")
        if any(value.startswith(("ff_", "fs_", "mdr_", "mdm_", "mce_", "mcp_")) for value in result):
            raise ValueError("recursive-determinant argument captures a generated binder")
        return result
    except ValueError as error:
        raise MatrixRecursiveDeterminantError(str(error)) from error


def _names(tag: str, *stems: str) -> tuple[str, ...]:
    safe = _safe(tag)
    return tuple(f"mdr_{stem}_{safe}" for stem in stems)


def _and(*parts: str) -> str:
    result = f"({parts[-1]})"
    for part in reversed(parts[:-1]):
        result = f"(({part}) /\\ {result})"
    return result


def _at(b: str, c: str, i: str, a: str, tag: str) -> str:
    return _beta_at_term(b, c, i, a, tag=f"mdr_{_safe(tag)}", avoid=())


def _lt(a: str, b: str, tag: str) -> str:
    (gap,) = _names(tag, "gap")
    return f"exists {gap}. {gap} + S ({a}) = ({b})"


def _le(a: str, b: str, tag: str) -> str:
    (gap,) = _names(tag, "gap")
    return f"exists {gap}. {gap} + ({a}) = ({b})"


def _code(d: str, pb: str, pc: str, nb: str, nc: str, p: str, n: str) -> str:
    # Balance all seven fields: nesting the matrix-four record inside two
    # additional pairs would needlessly multiply its expanded formula size.
    return _pair(_pack_four(d, pb, pc, nb), _pair(nc, _pair(p, n)))


def _node_code(z: str, d: str, pb: str, pc: str, nb: str, nc: str, p: str, n: str, tag: str) -> str:
    """Conservatively share the six pairing subterms by ordinary existentials."""
    a, b, c, e, f = _names(tag,'a','b','c','e','f')
    equations = _and(
        f"{a} = {_pair(d,pb)}", f"{b} = {_pair(pc,nb)}",
        f"{c} = {_pair(a,b)}", f"{e} = {_pair(p,n)}",
        f"{f} = {_pair(nc,e)}", f"({z}) = {_pair(c,f)}",
    )
    return f"exists {a} {b} {c} {e} {f}. {equations}"


def _record(b: str, c: str, i: str, d: str, pb: str, pc: str, nb: str, nc: str, p: str, n: str, tag: str) -> str:
    (z,) = _names(tag,'z')
    return f"exists {z}. {_and(_node_code(z,d,pb,pc,nb,nc,p,n,tag+'c'),_at(b,c,i,z,tag+'b'))}"


def _prefix(b: str, c: str, u: str, v: str, length: str, tag: str) -> str:
    i, a = _names(tag, "i", "a")
    return (
        f"forall {i} {a}. ({_lt(i,length,tag+'b')}) -> "
        f"({_at(b,c,i,a,tag+'o')}) -> ({_at(u,v,i,a,tag+'n')})"
    )


def _minor(pb: str, pc: str, nb: str, nc: str, q: str, j: str, up: str, us: str, un: str, ut: str, tag: str) -> str:
    return _signed_minor_terms(
        pb, pc, nb, nc, f"S ({q})", "0", j, q, up, us, un, ut,
        tag=f"mdr_{_safe(tag)}", avoid=(),
    )


def _children(
    b: str, c: str, limit: str, pb: str, pc: str, nb: str, nc: str,
    q: str, eb: str, ec: str, fb: str, fc: str, length: str, tag: str,
) -> str:
    j, i, up, us, un, ut, p, n = _names(tag, "j", "i", "up", "us", "un", "ut", "p", "n")
    parts = _and(
        _lt(i,limit,tag+'i'),
        _record(b,c,i,q,up,us,un,ut,p,n,tag+'r'),
        _minor(pb,pc,nb,nc,q,j,up,us,un,ut,tag+'m'),
        _at(eb,ec,j,p,tag+'p'),
        _at(fb,fc,j,n,tag+'n'),
    )
    return f"forall {j}. ({_lt(j,length,tag+'j')}) -> exists {i} {up} {us} {un} {ut} {p} {n}. {parts}"


def _step(b: str, c: str, i: str, d: str, pb: str, pc: str, nb: str, nc: str, p: str, n: str, tag: str) -> str:
    q, eb, ec, fb, fc = _names(tag, "q", "eb", "ec", "fb", "fc")
    base = _and(f"({d}) = 0", f"({p}) = 1", f"({n}) = 0")
    successor = _and(
        f"({d}) = S ({q})",
        _children(b,c,i,pb,pc,nb,nc,q,eb,ec,fb,fc,f"S ({q})",tag+'c'),
        _fold_terms(pb,pc,nb,nc,eb,ec,fb,fc,f"S ({q})",p,n,tag=f"mdr_{tag}f"),
    )
    return f"({base} \\/ exists {q} {eb} {ec} {fb} {fc}. {successor})"


def _history(b: str, c: str, length: str, tag: str) -> str:
    i, d, pb, pc, nb, nc, p, n = _names(tag, "i", "d", "pb", "pc", "nb", "nc", "p", "n")
    record = _record(b,c,i,d,pb,pc,nb,nc,p,n,tag+'r')
    step = _step(b,c,i,d,pb,pc,nb,nc,p,n,tag+'s')
    return f"forall {i}. ({_lt(i,length,tag+'i')}) -> exists {d} {pb} {pc} {nb} {nc} {p} {n}. {_and(record,step)}"


def _extension_result(
    d: str, pb: str, pc: str, nb: str, nc: str,
    b: str, c: str, length: str, u: str, v: str, last: str, p: str, n: str, tag: str,
) -> str:
    return _and(
        _prefix(b,c,u,v,length,tag+'p'),
        _le(length,last,tag+'l'),
        _history(u,v,f"S ({last})",tag+'h'),
        _record(u,v,last,d,pb,pc,nb,nc,p,n,tag+'r'),
    )


def _extend_property(d: str, tag: str) -> str:
    pb, pc, nb, nc, b, c, length, u, v, last, p, n = _names(
        tag, "pb", "pc", "nb", "nc", "b", "c", "l", "u", "v", "t", "p", "n"
    )
    result = _extension_result(d,pb,pc,nb,nc,b,c,length,u,v,last,p,n,tag+'r')
    return f"forall {pb} {pc} {nb} {nc} {b} {c} {length}. ({_history(b,c,length,tag+'h')}) -> exists {u} {v} {last} {p} {n}. {result}"


def _family_result(
    pb: str, pc: str, nb: str, nc: str, q: str, b: str, c: str, length: str,
    u: str, v: str, end: str, eb: str, ec: str, fb: str, fc: str, count: str, tag: str,
) -> str:
    return _and(
        _prefix(b,c,u,v,length,tag+'p'), _le(length,end,tag+'l'),
        _history(u,v,end,tag+'h'),
        _children(u,v,end,pb,pc,nb,nc,q,eb,ec,fb,fc,count,tag+'c'),
    )


def signed_determinant_node_code_relation(z: str, d: str, pb: str, pc: str, nb: str, nc: str, p: str, n: str, *, tag: str) -> str:
    """One exact injective record of dimension, actual matrix, and signed value."""
    z, d, pb, pc, nb, nc, p, n = _arguments(z,d,pb,pc,nb,nc,p,n)
    return _node_code(z,d,pb,pc,nb,nc,p,n,tag)


def signed_determinant_history_relation(b: str, c: str, length: str, *, tag: str) -> str:
    """A finite actual evaluation DAG, never an assumed recursive predicate."""
    return _history(*_arguments(b,c,length),tag)


def _det(pb: str, pc: str, nb: str, nc: str, d: str, p: str, n: str, tag: str) -> str:
    b, c, length, i = _names(tag,"b","c","l","i")
    return f"exists {b} {c} {length} {i}. {_and(_history(b,c,length,tag+'h'),_lt(i,length,tag+'i'),_record(b,c,i,d,pb,pc,nb,nc,p,n,tag+'r'))}"


def signed_recursive_determinant_relation(pb: str, pc: str, nb: str, nc: str, d: str, p: str, n: str, *, tag: str) -> str:
    """An actual root in a finite checked strict-child cofactor evaluation DAG."""
    pb, pc, nb, nc, d, p, n = _arguments(pb,pc,nb,nc,d,p,n)
    return _det(pb,pc,nb,nc,d,p,n,tag)


def _cofactors(pb: str, pc: str, nb: str, nc: str, q: str, eb: str, ec: str, fb: str, fc: str, tag: str) -> str:
    j, up, us, un, ut, p, n = _names(tag,'j','up','us','un','ut','p','n')
    return (
        f"forall {j}. ({_lt(j,f'S ({q})',tag+'j')}) -> exists {up} {us} {un} {ut} {p} {n}. "
        +_and(_minor(pb,pc,nb,nc,q,j,up,us,un,ut,tag+'m'),
              _det(up,us,un,ut,q,p,n,tag+'d'),_at(eb,ec,j,p,tag+'p'),_at(fb,fc,j,n,tag+'n'))
    )


def signed_evaluated_cofactor_relation(pb: str, pc: str, nb: str, nc: str, q: str, eb: str, ec: str, fb: str, fc: str, *, tag: str) -> str:
    """Every actual first-row minor has a genuine recursively evaluated value."""
    return _cofactors(*_arguments(pb,pc,nb,nc,q,eb,ec,fb,fc),tag)


def _intro(*names: str) -> tuple[str, ...]:
    return tuple(f"intro {name}" for name in names)


def _apply(name: str, *arguments: str) -> tuple[str, ...]:
    return tuple(f"specialize {name} ({argument})" for argument in arguments) + (f"apply {name}",)


def _cases(name: str, count: int) -> tuple[str, ...]:
    return tuple(f"cases {name}{'_witness' * index}" for index in range(count))


def _parts(name: str, count: int) -> tuple[str, ...]:
    return tuple(f"cases {name}{'_right' * index}" for index in range(count-1))


def _part(name: str, count: int, index: int) -> str:
    return f"{name}{'_right' * index}{'_left' if index < count-1 else ''}"


def _exists(*terms: str) -> tuple[str, ...]:
    return tuple(f"exists {term}" for term in terms)


def _rewrite_all(equation: str, variable: str, formula: str) -> tuple[str, ...]:
    count = len(re.findall(rf"(?<![\w']){re.escape(variable)}(?![\w'])", formula))
    return (f"rewrite {equation}",) * count


def make_matrix_recursive_determinant_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """Return dependency-ordered real proof scripts over immutable Alpha v26."""
    old_prefix = _prefix('b','c','u','v','l','source')
    old_history = _history('b','c','l','old')
    new_history = _history('u','v','l','new')
    fields = ('d','pb','pc','nb','nc','p','n')
    common = ('pb','pc','nb','nc','q','eb','ec','fb','fc','k')
    child_old = _children('b','c','l',*common,'old')
    child_new = _children('u','v','m',*common,'new')
    child_entry = _and(
        _lt('i','l','at_i'),
        _record('b','c','i','q','up','us','un','ut','a','z','at_r'),
        _minor('pb','pc','nb','nc','q','j','up','us','un','ut','at_m'),
        _at('eb','ec','j','a','at_p'),_at('fb','fc','j','z','at_n'),
    )
    record_h = 'hentry' + '_witness'*7
    step_h = 'hstep_right' + '_witness'*5
    hist_h = 'hentry' + '_witness'*7
    previous_h = 'hprevious' + '_witness'*7
    determinant_h = 'hdeterminant' + '_witness'*5
    minor_h = 'hminor' + '_witness'*4
    family_h = 'hfamily' + '_witness'*7
    other_fields = ('e','ab','ac','bb','bc','r','s')
    first_code_h = 'hfirst' + '_witness'*5
    second_code_h = 'hsecond' + '_witness'*5
    root_h = 'hdeterminant' + '_witness'*4
    local_h = 'hlocal_right' + '_witness'*5
    cofactor_result = _and(
        _cofactors('pb','pc','nb','nc','q','eb','ec','fb','fc','cofactor_result'),
        _fold_terms('pb','pc','nb','nc','eb','ec','fb','fc','S q','p','n',tag='mdr_cofactor_result'),
    )
    return (
        spec(
            'matrix_recursive_node_code_exists',
            f"forall {' '.join(fields)}. exists z. ({_node_code('z',*fields,'code_exists')})",
            (), _intro(*fields)
            +_exists(_code(*fields),_pair('d','pb'),_pair('pc','nb'),_pack_four('d','pb','pc','nb'),_pair('p','n'),_pair('nc',_pair('p','n')))
            +('split','refl','split','refl','split','refl','split','refl','split','refl','refl'),
            'Six explicit doubled-Cantor constructors code one exact matrix evaluation record with conservatively shared intermediate values.',
        ),
        spec(
            'matrix_recursive_prefix_refl',
            f"forall b c l. ({_prefix('b','c','b','c','l','refl')})",
            (), _intro('b','c','l','i','a','hi','ha')+('exact ha',),
            'A beta prefix is unchanged under its own exact code pair.',
        ),
        spec(
            'matrix_recursive_prefix_trans',
            f"forall b c u v w z l. ({old_prefix}) -> ({_prefix('u','v','w','z','l','middle')}) -> ({_prefix('b','c','w','z','l','result')})",
            (), _intro('b','c','u','v','w','z','l','hfirst','hsecond','i','a','hi','ha')
            +_apply('hsecond','i','a')+('exact hi',)+_apply('hfirst','i','a')+('exact hi','exact ha'),
            'Actual beta-prefix preservation composes without changing any encoded entry.',
        ),
        spec(
            'matrix_recursive_prefix_restrict',
            f"forall b c u v l k. ({_le('k','l','bound')}) -> ({old_prefix}) -> ({_prefix('b','c','u','v','k','short')})",
            ('lt_of_lt_of_le',), _intro('b','c','u','v','l','k','hk','hprefix','i','a','hi','ha')
            +_apply('hprefix','i','a')+_apply('lt_of_lt_of_le','i','k','l')+('exact hi','exact hk','exact ha'),
            'An exact preserved beta prefix restricts to every constructively bounded shorter prefix.',
        ),
        spec(
            'matrix_recursive_record_transport',
            f"forall b c u v l i {' '.join(fields)}. ({old_prefix}) -> ({_lt('i','l','record_bound')}) -> "
            f"({_record('b','c','i',*fields,'record_old')}) -> ({_record('u','v','i',*fields,'record_new')})",
            (), _intro('b','c','u','v','l','i',*fields,'hprefix','hi','hrecord')
            +_cases('hrecord',1)+_parts('hrecord_witness',2)+_exists('x')
            +('split','exact hrecord_witness_left')+_apply('hprefix','i','x')
            +('exact hi','exact hrecord_witness_right'),
            'Preserved beta entries carry the same actual seven-field evaluation record without expanding nested pairing polynomials.',
        ),
        spec(
            'matrix_recursive_record_append',
            f"forall b c l {' '.join(fields)}. exists u v. {_and(_prefix('b','c','u','v','l','record_append_p'),_record('u','v','l',*fields,'record_append_r'))}",
            ('matrix_recursive_node_code_exists','beta_prefix_extend'),
            _intro('b','c','l',*fields)
            +(f"have hcode : exists z. ({_node_code('z',*fields,'record_append_code')})",)
            +_apply('matrix_recursive_node_code_exists',*fields)+_cases('hcode',1)
            +(f"have hext : exists u v. {_and(_at('u','v','l','x','record_append_beta'),_prefix('b','c','u','v','l','record_append_preserve'))}",)
            +_apply('beta_prefix_extend','l','b','c','x')+_cases('hext',2)+_parts('hext_witness_witness',2)
            +_exists('x1','x2')+('split','exact hext_witness_witness_right')+_exists('x')
            +('split','exact hcode_witness','exact hext_witness_witness_left'),
            'An arbitrary actual evaluation record can be beta-appended without changing any previous record.',
        ),
        spec(
            'matrix_recursive_empty_history',
            f"forall b c. ({_history('b','c','0','empty')})",
            ('add_eq_zero_right','succ_ne_zero'),
            _intro('b','c','i','hi')+('exfalso','cases hi','have hzero : S i = 0')
            +_apply('add_eq_zero_right','x','S i')+('exact hi_witness',)+_apply('succ_ne_zero','i')+('exact hzero',),
            'The empty evaluation history has no unsupported matrix records.',
        ),
        spec(
            'matrix_recursive_children_transport',
            f"forall b c u v l m {' '.join(common)}. ({old_prefix}) -> ({_le('l','m','transport')}) -> ({child_old}) -> ({child_new})",
            ('lt_of_lt_of_le','matrix_recursive_record_transport'),
            _intro('b','c','u','v','l','m',*common,'hprefix','hlm','hchildren','j','hj')
            +(f"have hentry : exists i up us un ut a z. {child_entry}",)
            +_apply('hchildren','j')+('exact hj',)+_cases('hentry',7)+_parts(record_h,5)
            +_exists('x','x1','x2','x3','x4','x5','x6')+('split',)
            +_apply('lt_of_lt_of_le','x','l','m')+(f"exact {_part(record_h,5,0)}",'exact hlm','split')
            +_apply('matrix_recursive_record_transport','b','c','u','v','l','x','q','x1','x2','x3','x4','x5','x6')
            +('exact hprefix',f"exact {_part(record_h,5,0)}",f"exact {_part(record_h,5,1)}",'split',f"exact {_part(record_h,5,2)}",'split',f"exact {_part(record_h,5,3)}",f"exact {_part(record_h,5,4)}"),
            'Every actual smaller-matrix child remains present when its evaluation DAG is extended.',
        ),
        spec(
            'matrix_recursive_step_transport',
            f"forall b c u v i {' '.join(fields)}. ({_prefix('b','c','u','v','i','step_prefix')}) -> ({_step('b','c','i',*fields,'old_step')}) -> ({_step('u','v','i',*fields,'new_step')})",
            ('le_refl','matrix_recursive_children_transport'),
            _intro('b','c','u','v','i',*fields,'hprefix','hstep')+('cases hstep','left','exact hstep_left','right')
            +_cases('hstep_right',5)+_parts(step_h,3)+_exists('x','x1','x2','x3','x4')
            +('split',f"exact {_part(step_h,3,0)}",'split')
            +_apply('matrix_recursive_children_transport','b','c','u','v','i','i','pb','pc','nb','nc','x','x1','x2','x3','x4','S x')
            +('exact hprefix','apply le_refl',f"exact {_part(step_h,3,1)}",f"exact {_part(step_h,3,2)}"),
            'A genuine local cofactor evaluation transports along preservation of all strictly earlier records.',
        ),
        spec(
            'matrix_recursive_history_transport',
            f"forall b c u v l. ({old_prefix}) -> ({old_history}) -> ({new_history})",
            ('lt_trans','matrix_recursive_record_transport','matrix_recursive_step_transport'),
            _intro('b','c','u','v','l','hprefix','hhistory','i','hi')
            +(f"have hentry : exists {' '.join(fields)}. {_and(_record('b','c','i',*fields,'entry_r'),_step('b','c','i',*fields,'entry_s'))}",)
            +_apply('hhistory','i')+('exact hi',)+_cases('hentry',7)+_parts(hist_h,2)
            +_exists('x','x1','x2','x3','x4','x5','x6')+('split',)
            +_apply('matrix_recursive_record_transport','b','c','u','v','l','i','x','x1','x2','x3','x4','x5','x6')+('exact hprefix','exact hi',f"exact {hist_h}_left")
            +_apply('matrix_recursive_step_transport','b','c','u','v','i','x','x1','x2','x3','x4','x5','x6')
            +_intro('j','a','hj','ha')+_apply('hprefix','j','a')+_apply('lt_trans','j','i','l')
            +('exact hj','exact hi','exact ha',f"exact {hist_h}_right"),
            'A finite genuine determinant history is invariant under exact preservation of its beta-coded records.',
        ),
        spec(
            'matrix_recursive_history_extend',
            f"forall b c l {' '.join(fields)}. ({old_history}) -> ({_step('b','c','l',*fields,'append_s')}) -> exists u v. "
            +_and(_prefix('b','c','u','v','l','append_p'),_history('u','v','S l','append_h'),_record('u','v','l',*fields,'append_r')),
            ('matrix_recursive_record_append','finite_lt_succ_eq_or_lt','matrix_recursive_history_transport','matrix_recursive_step_transport'),
            _intro('b','c','l',*fields,'hhistory','hstep')
            +(f"have hext : exists u v. {_and(_prefix('b','c','u','v','l','beta_preserve'),_record('u','v','l',*fields,'beta_append'))}",)
            +_apply('matrix_recursive_record_append','b','c','l',*fields)
            +_cases('hext',2)+_parts('hext_witness_witness',2)
            +(f"have hnewhistory : {_history('x','x1','l','app_history')}",)
            +_apply('matrix_recursive_history_transport','b','c','x','x1','l')
            +('exact hext_witness_witness_left','exact hhistory',f"have hnewstep : {_step('x','x1','l',*fields,'app_step')}")
            +_apply('matrix_recursive_step_transport','b','c','x','x1','l',*fields)
            +('exact hext_witness_witness_left','exact hstep')+_exists('x','x1')
            +('split','exact hext_witness_witness_left','split')
            +_intro('i','hi')+('have hsplit : i = l \\/ exists gap. gap + S i = l',)
            +_apply('finite_lt_succ_eq_or_lt','l','i')+('exact hi','cases hsplit')
            +_exists(*fields)+('split',)
            +_rewrite_all('hsplit_left','i',_record('x','x1','i',*fields,'rw_record'))
            +('exact hext_witness_witness_right',)
            +_rewrite_all('hsplit_left','i',_step('x','x1','i',*fields,'rw_step'))
            +('exact hnewstep',)+_apply('hnewhistory','i')+('exact hsplit_right','exact hext_witness_witness_right'),
            'Append one genuinely evaluated matrix node while preserving every earlier record and every strict-child certificate.',
        ),
        spec(
            'matrix_recursive_zero_extension',
            _extend_property('0','zero_extension'),
            ('le_refl','matrix_recursive_history_extend'),
            _intro('pb','pc','nb','nc','b','c','l','hhistory')
            +(f"have hext : exists u v. {_and(_prefix('b','c','u','v','l','zero_p'),_history('u','v','S l','zero_h'),_record('u','v','l','0','pb','pc','nb','nc','1','0','zero_r'))}",)
            +_apply('matrix_recursive_history_extend','b','c','l','0','pb','pc','nb','nc','1','0')
            +('exact hhistory','left','split','refl','split','refl','refl')
            +_cases('hext',2)+_parts('hext_witness_witness',3)+_exists('x','x1','l','1','0')
            +('split',f"exact {_part('hext_witness_witness',3,0)}",'split','apply le_refl','split',f"exact {_part('hext_witness_witness',3,1)}",f"exact {_part('hext_witness_witness',3,2)}"),
            'Every existing valid evaluation DAG can be extended by the exact empty determinant (1,0).',
        ),
        spec(
            'matrix_recursive_children_empty',
            f"forall b c l pb pc nb nc q eb ec fb fc. ({_children('b','c','l','pb','pc','nb','nc','q','eb','ec','fb','fc','0','empty_children')})",
            ('add_eq_zero_right','succ_ne_zero'),
            _intro('b','c','l','pb','pc','nb','nc','q','eb','ec','fb','fc','j','hj')
            +('exfalso','cases hj','have hzero : S j = 0')+_apply('add_eq_zero_right','x','S j')
            +('exact hj_witness',)+_apply('succ_ne_zero','j')+('exact hzero',),
            'The empty minor-value prefix makes no unproved determinant claim.',
        ),
        spec(
            'matrix_recursive_children_recode',
            f"forall b c l {' '.join(common)} ub uc vb vc. ({child_old}) -> "
            f"({_prefix('eb','ec','ub','uc','k','recode_p')}) -> ({_prefix('fb','fc','vb','vc','k','recode_n')}) -> "
            f"({_children('b','c','l','pb','pc','nb','nc','q','ub','uc','vb','vc','k','recoded')})",
            (),
            _intro('b','c','l',*common,'ub','uc','vb','vc','hchildren','hpositive','hnegative','j','hj')
            +(f"have hentry : exists i up us un ut a z. {child_entry}",)
            +_apply('hchildren','j')+('exact hj',)+_cases('hentry',7)+_parts(record_h,5)
            +_exists('x','x1','x2','x3','x4','x5','x6')
            +('split',f"exact {_part(record_h,5,0)}",'split',f"exact {_part(record_h,5,1)}",'split',f"exact {_part(record_h,5,2)}",'split')
            +_apply('hpositive','j','x5')+('exact hj',f"exact {_part(record_h,5,3)}")
            +_apply('hnegative','j','x6')+('exact hj',f"exact {_part(record_h,5,4)}"),
            'Reencoding the two already computed cofactor-value streams preserves every actual minor evaluation.',
        ),
        spec(
            'matrix_recursive_children_extend',
            f"forall b c l {' '.join(common)} i up us un ut a z. ({child_old}) -> "
            f"({_lt('i','l','append_child_bound')}) -> ({_record('b','c','i','q','up','us','un','ut','a','z','append_child_record')}) -> "
            f"({_minor('pb','pc','nb','nc','q','k','up','us','un','ut','append_child_minor')}) -> exists ub uc vb vc. "
            f"({_children('b','c','l','pb','pc','nb','nc','q','ub','uc','vb','vc','S k','append_children')})",
            ('beta_prefix_extend','finite_lt_succ_eq_or_lt','matrix_recursive_children_recode'),
            _intro('b','c','l',*common,'i','up','us','un','ut','a','z','hchildren','hi','hrecord','hminor')
            +(f"have hpos : exists ub uc. {_and(_at('ub','uc','k','a','append_pos'),_prefix('eb','ec','ub','uc','k','append_pos_preserve'))}",)
            +_apply('beta_prefix_extend','k','eb','ec','a')+_cases('hpos',2)+_parts('hpos_witness_witness',2)
            +(f"have hneg : exists vb vc. {_and(_at('vb','vc','k','z','append_neg'),_prefix('fb','fc','vb','vc','k','append_neg_preserve'))}",)
            +_apply('beta_prefix_extend','k','fb','fc','z')+_cases('hneg',2)+_parts('hneg_witness_witness',2)
            +(f"have hrecoded : {_children('b','c','l','pb','pc','nb','nc','q','x','x1','x2','x3','k','append_recoded')}",)
            +_apply('matrix_recursive_children_recode','b','c','l',*common,'x','x1','x2','x3')
            +('exact hchildren','exact hpos_witness_witness_right','exact hneg_witness_witness_right')
            +_exists('x','x1','x2','x3')+_intro('j','hj')
            +('have hsplit : j = k \\/ exists gap. gap + S j = k',)
            +_apply('finite_lt_succ_eq_or_lt','k','j')+('exact hj','cases hsplit')
            +_exists('i','up','us','un','ut','a','z')
            +('split','exact hi','split','exact hrecord','split')
            +_rewrite_all('hsplit_left','j',_minor('pb','pc','nb','nc','q','j','up','us','un','ut','rw_minor'))
            +('exact hminor','split')
            +_rewrite_all('hsplit_left','j',_at('x','x1','j','a','rw_positive'))
            +('exact hpos_witness_witness_left',)
            +_rewrite_all('hsplit_left','j',_at('x2','x3','j','z','rw_negative'))
            +('exact hneg_witness_witness_left',)+_apply('hrecoded','j')+('exact hsplit_right',),
            'Append one actual smaller determinant to the cofactor streams, preserving all previously certified columns.',
        ),
        spec(
            'matrix_recursive_cofactor_prefix_from_recursion',
            f"forall q pb pc nb nc b c l k. ({_extend_property('q','recursion')}) -> ({_le('k','S q','columns')}) -> ({old_history}) -> "
            f"exists u v m eb ec fb fc. ({_family_result('pb','pc','nb','nc','q','b','c','l','u','v','m','eb','ec','fb','fc','k','family_result')})",
            ('le_refl','le_succ','le_trans','beta_signed_matrix_minor_exists',
             'matrix_recursive_prefix_refl','matrix_recursive_prefix_restrict','matrix_recursive_prefix_trans',
             'matrix_recursive_children_empty','matrix_recursive_children_transport','matrix_recursive_children_extend'),
            _intro('q','pb','pc','nb','nc','b','c','l')+('induction k',)
            +_intro('hrecursion','hbound','hhistory')+_exists('b','c','l','0','0','0','0')
            +('split',)+_apply('matrix_recursive_prefix_refl','b','c','l')
            +('split','apply le_refl','split','exact hhistory')
            +_apply('matrix_recursive_children_empty','b','c','l','pb','pc','nb','nc','q','0','0','0','0')
            +_intro('hrecursion','hbound','hhistory')
            +(f"have hsuccessor : {_le('k','S k','column_successor')}",)
            +_apply('le_succ','k','k')+('apply le_refl',f"have hshort : {_le('k','S q','short_columns')}")
            +_apply('le_trans','k','S k','S q')+('exact hsuccessor','exact hbound')
            +(f"have hprevious : exists u v m eb ec fb fc. ({_family_result('pb','pc','nb','nc','q','b','c','l','u','v','m','eb','ec','fb','fc','k','previous')})",)
            +('apply IH','exact hrecursion','exact hshort','exact hhistory')
            +_cases('hprevious',7)+_parts(previous_h,4)
            +(f"have hrow : {_lt('0','S q','first_row')}",'exists q','simp')
            +(f"have hminor : exists up us un ut. ({_minor('pb','pc','nb','nc','q','k','up','us','un','ut','actual_minor')})",)
            +_apply('beta_signed_matrix_minor_exists','pb','pc','nb','nc','q','0','k')
            +('exact hrow','exact hbound')+_cases('hminor',4)
            +(f"have hdeterminant : exists u v t p n. ({_extension_result('q','x7','x8','x9','x10','x','x1','x2','u','v','t','p','n','child_eval')})",)
            +_apply('hrecursion','x7','x8','x9','x10','x','x1','x2')
            +(f"exact {_part(previous_h,4,2)}",)+_cases('hdeterminant',5)+_parts(determinant_h,4)
            +(f"have hendbound : {_le('x2','S x13','child_end')}",)
            +_apply('le_succ','x2','x13')+(f"exact {_part(determinant_h,4,1)}",)
            +(f"have htransported : {_children('x11','x12','S x13','pb','pc','nb','nc','q','x3','x4','x5','x6','k','old_children_new_trace')}",)
            +_apply('matrix_recursive_children_transport','x','x1','x11','x12','x2','S x13','pb','pc','nb','nc','q','x3','x4','x5','x6','k')
            +(f"exact {_part(determinant_h,4,0)}",'exact hendbound',f"exact {_part(previous_h,4,3)}")
            +(f"have hnew : exists eb ec fb fc. ({_children('x11','x12','S x13','pb','pc','nb','nc','q','eb','ec','fb','fc','S k','new_children')})",)
            +_apply('matrix_recursive_children_extend','x11','x12','S x13','pb','pc','nb','nc','q','x3','x4','x5','x6','k','x13','x7','x8','x9','x10','x14','x15')
            +('exact htransported','apply le_refl',f"exact {_part(determinant_h,4,3)}",f"exact {minor_h}")
            +_cases('hnew',4)+_exists('x11','x12','S x13','x16','x17','x18','x19')+('split',)
            +_apply('matrix_recursive_prefix_trans','b','c','x','x1','x11','x12','l')
            +(f"exact {_part(previous_h,4,0)}",)
            +_apply('matrix_recursive_prefix_restrict','x','x1','x11','x12','x2','l')
            +(f"exact {_part(previous_h,4,1)}",f"exact {_part(determinant_h,4,0)}",'split')
            +_apply('le_trans','l','x2','S x13')+(f"exact {_part(previous_h,4,1)}",'exact hendbound','split',f"exact {_part(determinant_h,4,2)}",f"exact hnew{'_witness'*4}"),
            'Dimension recursion constructs every genuine cofactor determinant in one shared history, by finite prefix induction; the recursion premise is later discharged by HA induction.',
        ),
        spec(
            'matrix_recursive_successor_extension',
            f"forall q. ({_extend_property('q','rec_source')}) -> ({_extend_property('S q','rec_result')})",
            ('le_refl','signed_alternating_cofactor_fold_exists',
             'matrix_recursive_cofactor_prefix_from_recursion','matrix_recursive_history_extend',
             'matrix_recursive_prefix_trans','matrix_recursive_prefix_restrict'),
            _intro('q','hrecursion','pb','pc','nb','nc','b','c','l','hhistory')
            +(f"have hfamily : exists u v m eb ec fb fc. ({_family_result('pb','pc','nb','nc','q','b','c','l','u','v','m','eb','ec','fb','fc','S q','complete_family')})",)
            +_apply('matrix_recursive_cofactor_prefix_from_recursion','q','pb','pc','nb','nc','b','c','l','S q')
            +('exact hrecursion','apply le_refl','exact hhistory')+_cases('hfamily',7)+_parts(family_h,4)
            +(f"have hfold : exists p n. ({_fold_terms('pb','pc','nb','nc','x3','x4','x5','x6','S q','p','n',tag='mdr_complete_fold')})",)
            +_apply('signed_alternating_cofactor_fold_exists','pb','pc','nb','nc','x3','x4','x5','x6','S q')
            +_cases('hfold',2)
            +(f"have hext : exists u v. {_and(_prefix('x','x1','u','v','x2','root_prefix'),_history('u','v','S x2','root_history'),_record('u','v','x2','S q','pb','pc','nb','nc','x7','x8','root_record'))}",)
            +_apply('matrix_recursive_history_extend','x','x1','x2','S q','pb','pc','nb','nc','x7','x8')
            +(f"exact {_part(family_h,4,2)}",'right')+_exists('q','x3','x4','x5','x6')
            +('split','refl','split',f"exact {_part(family_h,4,3)}",'exact hfold_witness_witness')
            +_cases('hext',2)+_parts('hext_witness_witness',3)
            +_exists('x9','x10','x2','x7','x8')+('split',)
            +_apply('matrix_recursive_prefix_trans','b','c','x','x1','x9','x10','l')
            +(f"exact {_part(family_h,4,0)}",)
            +_apply('matrix_recursive_prefix_restrict','x','x1','x9','x10','x2','l')
            +(f"exact {_part(family_h,4,1)}",f"exact {_part('hext_witness_witness',3,0)}",'split',f"exact {_part(family_h,4,1)}",'split',f"exact {_part('hext_witness_witness',3,1)}",f"exact {_part('hext_witness_witness',3,2)}"),
            'If every dimension-q matrix can be genuinely evaluated, every dimension-(q+1) matrix can be appended using all q-dimensional minors and its exact signed Laplace sum.',
        ),
        spec(
            'matrix_recursive_all_extensions',
            f"forall d. ({_extend_property('d','all_dimensions')})",
            ('matrix_recursive_zero_extension','matrix_recursive_successor_extension'),
            ('induction d','exact matrix_recursive_zero_extension')
            +_apply('matrix_recursive_successor_extension','d')+('exact IH',),
            'Unrestricted first-order induction proves genuine determinant evaluation can extend every valid finite history, for every natural dimension.',
        ),
        spec(
            'signed_recursive_determinant_exists',
            f"forall pb pc nb nc d. exists p n. ({signed_recursive_determinant_relation('pb','pc','nb','nc','d','p','n',tag='det_exists')})",
            ('le_refl','matrix_recursive_empty_history','matrix_recursive_all_extensions'),
            _intro('pb','pc','nb','nc','d')
            +(f"have hevaluation : exists u v t p n. ({_extension_result('d','pb','pc','nb','nc','0','0','0','u','v','t','p','n','existence_eval')})",)
            +_apply('matrix_recursive_all_extensions','d','pb','pc','nb','nc','0','0','0')
            +_apply('matrix_recursive_empty_history','0','0')
            +_cases('hevaluation',5)+_parts('hevaluation'+'_witness'*5,4)
            +_exists('x3','x4','x','x1','S x2','x2')
            +('split',f"exact {_part('hevaluation'+'_witness'*5,4,2)}",'split','apply le_refl',f"exact {_part('hevaluation'+'_witness'*5,4,3)}"),
            'Every signed beta-coded square matrix has an actual finite strictly well-founded cofactor evaluation, with no bound on dimension and no assumed determinant oracle.',
        ),
        spec(
            'matrix_recursive_node_code_injective',
            f"forall z {' '.join(fields)} {' '.join(other_fields)}. ({_node_code('z',*fields,'code_first')}) -> ({_node_code('z',*other_fields,'code_second')}) -> "
            +_and(*(f"{a} = {b}" for a,b in zip(fields,other_fields))),
            ('pair_code_injective',),
            _intro('z',*fields,*other_fields,'hfirst','hsecond')
            +_cases('hfirst',5)+_parts(first_code_h,6)+_cases('hsecond',5)+_parts(second_code_h,6)
            +('have hroot : x2 = x7 /\\ x4 = x9',)
            +_apply('pair_code_injective','z','x2','x4','x7','x9')
            +(f"exact {_part(first_code_h,6,5)}",f"exact {_part(second_code_h,6,5)}",'cases hroot')
            +('have hleft : x = x5 /\\ x1 = x6',)
            +_apply('pair_code_injective','x2','x','x1','x5','x6')
            +(f"exact {_part(first_code_h,6,2)}",'trans x7','exact hroot_left',f"exact {_part(second_code_h,6,2)}",'cases hleft')
            +('have hfirsttwo : d = e /\\ pb = ab',)
            +_apply('pair_code_injective','x','d','pb','e','ab')
            +(f"exact {_part(first_code_h,6,0)}",'trans x5','exact hleft_left',f"exact {_part(second_code_h,6,0)}",'cases hfirsttwo')
            +('have hnexttwo : pc = ac /\\ nb = bb',)
            +_apply('pair_code_injective','x1','pc','nb','ac','bb')
            +(f"exact {_part(first_code_h,6,1)}",'trans x6','exact hleft_right',f"exact {_part(second_code_h,6,1)}",'cases hnexttwo')
            +('have hright : nc = bc /\\ x3 = x8',)
            +_apply('pair_code_injective','x4','nc','x3','bc','x8')
            +(f"exact {_part(first_code_h,6,4)}",'trans x9','exact hroot_right',f"exact {_part(second_code_h,6,4)}",'cases hright')
            +('have hvalues : p = r /\\ n = s',)
            +_apply('pair_code_injective','x3','p','n','r','s')
            +(f"exact {_part(first_code_h,6,3)}",'trans x8','exact hright_right',f"exact {_part(second_code_h,6,3)}",'cases hvalues')
            +('split','exact hfirsttwo_left','split','exact hfirsttwo_right','split','exact hnexttwo_left','split','exact hnexttwo_right','split','exact hright_left','split','exact hvalues_left','exact hvalues_right'),
            'The conservatively shared record determines all seven actual matrix/dimension/value fields uniquely, by six independently checked pairing injections.',
        ),
        spec(
            'matrix_recursive_record_injective',
            f"forall b c i {' '.join(fields)} {' '.join(other_fields)}. ({_record('b','c','i',*fields,'record_first')}) -> ({_record('b','c','i',*other_fields,'record_second')}) -> "
            +_and(*(f"{a} = {b}" for a,b in zip(fields,other_fields))),
            ('beta_at_unique','matrix_recursive_node_code_injective'),
            _intro('b','c','i',*fields,*other_fields,'hfirst','hsecond')
            +_cases('hfirst',1)+_parts('hfirst_witness',2)+_cases('hsecond',1)+_parts('hsecond_witness',2)
            +('have hequal : x = x1',)+_apply('beta_at_unique','b','c','i','x','x1')
            +('exact hfirst_witness_right','exact hsecond_witness_right')
            +_apply('matrix_recursive_node_code_injective','x',*fields,*other_fields)
            +('exact hfirst_witness_left','rewrite hequal','exact hsecond_witness_left'),
            'A single actual beta entry cannot be interpreted as two different matrix evaluation records.',
        ),
        spec(
            'matrix_recursive_history_step_at',
            f"forall b c l i {' '.join(fields)}. ({old_history}) -> ({_lt('i','l','step_at_bound')}) -> "
            f"({_record('b','c','i',*fields,'step_at_record')}) -> ({_step('b','c','i',*fields,'step_at_result')})",
            ('matrix_recursive_record_injective',),
            _intro('b','c','l','i',*fields,'hhistory','hi','hrecord')
            +(f"have hentry : exists {' '.join(fields)}. {_and(_record('b','c','i',*fields,'step_entry_r'),_step('b','c','i',*fields,'step_entry_s'))}",)
            +_apply('hhistory','i')+('exact hi',)+_cases('hentry',7)+_parts(hist_h,2)
            +(f"have hequalities : {_and(*(f'{a} = {b}' for a,b in zip(fields,('x','x1','x2','x3','x4','x5','x6'))))}",)
            +_apply('matrix_recursive_record_injective','b','c','i',*fields,'x','x1','x2','x3','x4','x5','x6')
            +('exact hrecord',f"exact {hist_h}_left")+_parts('hequalities',7)
            +tuple(command for index,field in enumerate(fields) for command in _rewrite_all(_part('hequalities',7,index),field,_step('b','c','i',*fields,'step_rewrite')))
            +(f"exact {hist_h}_right",),
            'Every decoded in-range root of a genuine history satisfies its own actual cofactor rule, not merely a different record with the same code.',
        ),
        spec(
            'signed_recursive_determinant_zero_value',
            f"forall pb pc nb nc p n. ({_det('pb','pc','nb','nc','0','p','n','zero_value')}) -> p = 1 /\\ n = 0",
            ('succ_ne_zero','matrix_recursive_history_step_at'),
            _intro('pb','pc','nb','nc','p','n','hdeterminant')+_cases('hdeterminant',4)+_parts(root_h,3)
            +(f"have hlocal : {_step('x','x1','x3','0','pb','pc','nb','nc','p','n','zero_local')}",)
            +_apply('matrix_recursive_history_step_at','x','x1','x2','x3','0','pb','pc','nb','nc','p','n')
            +(f"exact {_part(root_h,3,0)}",f"exact {_part(root_h,3,1)}",f"exact {_part(root_h,3,2)}",'cases hlocal','cases hlocal_left','exact hlocal_left_right')
            +_cases('hlocal_right',5)+_parts('hlocal_right'+'_witness'*5,3)
            +('exfalso',)+_apply('succ_ne_zero','x4')+('symm',f"exact {_part('hlocal_right'+'_witness'*5,3,0)}"),
            'Every genuine zero-dimensional determinant has exactly the empty product value (1,0), with no exceptional code or trace boundary.',
        ),
        spec(
            'signed_recursive_determinant_successor_decomposition',
            f"forall pb pc nb nc q p n. ({_det('pb','pc','nb','nc','S q','p','n','successor_source')}) -> exists eb ec fb fc. {cofactor_result}",
            ('succ_ne_zero','lt_trans','matrix_recursive_history_step_at'),
            _intro('pb','pc','nb','nc','q','p','n','hdeterminant')+_cases('hdeterminant',4)+_parts(root_h,3)
            +(f"have hlocal : {_step('x','x1','x3','S q','pb','pc','nb','nc','p','n','successor_local')}",)
            +_apply('matrix_recursive_history_step_at','x','x1','x2','x3','S q','pb','pc','nb','nc','p','n')
            +(f"exact {_part(root_h,3,0)}",f"exact {_part(root_h,3,1)}",f"exact {_part(root_h,3,2)}",'cases hlocal','cases hlocal_left','exfalso')
            +_apply('succ_ne_zero','q')+('exact hlocal_left_left',)
            +_cases('hlocal_right',5)+_parts(local_h,3)
            +('have hdimension : q = x4','apply PA2',f"exact {_part(local_h,3,0)}")
            +_rewrite_all('hdimension','q',cofactor_result)+_exists('x5','x6','x7','x8')+('split',)
            +_intro('j','hj')
            +(f"have hchild : exists i up us un ut a z. {_and(_lt('i','x3','child_index'),_record('x','x1','i','x4','up','us','un','ut','a','z','child_record'),_minor('pb','pc','nb','nc','x4','j','up','us','un','ut','child_minor'),_at('x5','x6','j','a','child_positive'),_at('x7','x8','j','z','child_negative'))}",)
            +_apply(_part(local_h,3,1),'j')+('exact hj',)+_cases('hchild',7)+_parts('hchild'+'_witness'*7,5)
            +_exists('x10','x11','x12','x13','x14','x15')
            +('split',f"exact {_part('hchild'+'_witness'*7,5,2)}",'split')
            +_exists('x','x1','x2','x9')+('split',f"exact {_part(root_h,3,0)}",'split')
            +_apply('lt_trans','x9','x3','x2')+(f"exact {_part('hchild'+'_witness'*7,5,0)}",f"exact {_part(root_h,3,1)}",f"exact {_part('hchild'+'_witness'*7,5,1)}",'split',f"exact {_part('hchild'+'_witness'*7,5,3)}",f"exact {_part('hchild'+'_witness'*7,5,4)}",f"exact {_part(local_h,3,2)}"),
            'Every nonempty determinant is exactly the parity-correct Laplace fold of genuine recursively evaluated first-row minors; each child inherits an actual valid strict history.',
        ),
    )


__all__ = [
    'MatrixRecursiveDeterminantError',
    'signed_determinant_node_code_relation',
    'signed_determinant_history_relation',
    'signed_recursive_determinant_relation',
    'signed_evaluated_cofactor_relation',
    'make_matrix_recursive_determinant_candidate_theorems',
]
