"""Private reverse cell-history seed for native Peano arithmetic.

``CellHistory(z,l;b,c)`` is an untrusted authoring abbreviation.  It expands
immediately to a beta-coded reverse trace whose zero entry is nil, whose
``l`` entry is ``z``, and whose every bounded adjacent edge is an exact D06
cell.  If the values at ``i`` and ``S i`` are respectively ``t`` and ``u``,
the edge records ``Cell(u,h,t)`` for some head ``h``.

The dependency-ordered candidate tranche proves the empty-history seed,
one-cell extension through the already reviewed beta-prefix constructor, and
successor elimination with the original beta witnesses.  Every result is
dependency-curried, unregistered, and unadmitted.

The extension row deliberately uses the reviewed beta/CRT spine.  This places
the tranche in the post-K4/M3 ``K3B`` bridge, not in the 96-row strict-K3
foundation.
"""

from __future__ import annotations

from typing import Any, Callable


_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _identifier(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not (value[0].isalpha() or value[0] == "_")
        or not all(
            character.isalnum() or character in "_'"
            for character in value[1:]
        )
        or value in _RESERVED
    ):
        raise ValueError(f"{label} must be a non-reserved Peano identifier")
    return value


def _binders(
    tag: str,
    avoid: tuple[str, ...],
    roles: tuple[str, ...],
) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"hch_{role}_{safe_tag}" for role in roles)
    if len(set(names)) != len(names) or set(names) & set(avoid):
        raise ValueError("generated cell-history binder captures an argument")
    return names


def _beta_at_term(
    code: str,
    scale: str,
    index: str,
    value: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    height, quotient = _binders(tag, avoid, ("beta_height", "beta_quotient"))
    modulus = f"S ((S ({index})) * {scale})"
    return (
        f"((exists {height}. {height} + S ({value}) = {modulus}) /\\ "
        f"exists {quotient}. {code} = {quotient} * {modulus} + ({value}))"
    )


def beta_at(
    code: str,
    scale: str,
    index: str,
    value: str,
    *,
    tag: str,
) -> str:
    """Expand the checked ``BetaAt(code,scale,index,value)`` convention."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (code, "trace code"),
            (scale, "trace scale"),
            (index, "trace index"),
            (value, "decoded value"),
        )
    )
    return _beta_at_term(
        code,
        scale,
        index,
        value,
        tag=tag,
        avoid=variables,
    )


def _cell_term(code: str, head: str, tail: str) -> str:
    return (
        f"{code} = S (({head} + {tail}) * S ({head} + {tail}) + "
        f"({tail} + {tail}))"
    )


def _cell_history_term(
    code: str,
    length: str,
    trace_code: str,
    trace_scale: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    index, gap, tail, successor, head = _binders(
        tag,
        avoid,
        ("index", "gap", "tail", "successor", "head"),
    )
    local = avoid + (index, gap, tail, successor, head)
    start = _beta_at_term(
        trace_code,
        trace_scale,
        "0",
        "0",
        tag=f"{tag}_start",
        avoid=local,
    )
    terminal = _beta_at_term(
        trace_code,
        trace_scale,
        length,
        code,
        tag=f"{tag}_terminal",
        avoid=local,
    )
    current = _beta_at_term(
        trace_code,
        trace_scale,
        index,
        tail,
        tag=f"{tag}_current",
        avoid=local,
    )
    following = _beta_at_term(
        trace_code,
        trace_scale,
        f"S {index}",
        successor,
        tag=f"{tag}_following",
        avoid=local,
    )
    bound = f"exists {gap}. {gap} + S {index} = {length}"
    edge = _cell_term(successor, head, tail)
    return (
        f"(({start}) /\\ (({terminal}) /\\ forall {index}. ({bound}) -> "
        f"exists {tail} {successor} {head}. "
        f"(({current}) /\\ (({following}) /\\ ({edge})))))"
    )


def cell_history(
    code: str,
    length: str,
    trace_code: str,
    trace_scale: str,
    *,
    tag: str,
) -> str:
    """Expand ``CellHistory(code,length;trace_code,trace_scale)`` hygienically."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (code, "terminal cell code"),
            (length, "trace length"),
            (trace_code, "trace code"),
            (trace_scale, "trace scale"),
        )
    )
    return _cell_history_term(
        code,
        length,
        trace_code,
        trace_scale,
        tag=tag,
        avoid=variables,
    )


def cell_list_len(code: str, length: str, *, tag: str) -> str:
    """Expand existence of a reverse cell history of the displayed length."""

    variables = (
        _identifier(code, "terminal cell code"),
        _identifier(length, "trace length"),
    )
    trace_code, trace_scale = _binders(
        tag,
        variables,
        ("trace_code", "trace_scale"),
    )
    history = _cell_history_term(
        code,
        length,
        trace_code,
        trace_scale,
        tag=f"{tag}_history",
        avoid=variables + (trace_code, trace_scale),
    )
    return f"exists {trace_code} {trace_scale}. ({history})"


def make_ha_cell_history_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the reverse-history seed, extension, and elimination rows."""

    history = _cell_history_term(
        "0",
        "0",
        "0",
        "0",
        tag="nil_history",
        avoid=(),
    )
    extend_avoid = ("b", "c", "l", "t", "u", "h")
    extend_before = _cell_history_term(
        "t",
        "l",
        "b",
        "c",
        tag="extend_before",
        avoid=extend_avoid,
    )
    extend_after = _cell_history_term(
        "u",
        "S l",
        "b2",
        "c2",
        tag="extend_after",
        avoid=extend_avoid + ("b2", "c2"),
    )
    extend_cell = _cell_term("u", "h", "t")
    extend_hold_avoid = extend_avoid + ("i", "t0", "u0", "h0")
    extend_hold_current = _beta_at_term(
        "b",
        "c",
        "i",
        "t0",
        tag="extend_hold_current",
        avoid=extend_hold_avoid,
    )
    extend_hold_following = _beta_at_term(
        "b",
        "c",
        "S i",
        "u0",
        tag="extend_hold_following",
        avoid=extend_hold_avoid,
    )
    extend_hold = (
        f"exists t0 u0 h0. (({extend_hold_current}) /\\ "
        f"(({extend_hold_following}) /\\ ({_cell_term('u0', 'h0', 't0')})))"
    )

    elim_avoid = ("b", "c", "l", "u")
    elim_before = _cell_history_term(
        "u",
        "S l",
        "b",
        "c",
        tag="succ_elim_before",
        avoid=elim_avoid,
    )
    elim_after = _cell_history_term(
        "t",
        "l",
        "b",
        "c",
        tag="succ_elim_after",
        avoid=elim_avoid + ("t", "h"),
    )
    elim_last_avoid = elim_avoid + ("t", "u0", "h")
    elim_last_current = _beta_at_term(
        "b",
        "c",
        "l",
        "t",
        tag="succ_elim_last_current",
        avoid=elim_last_avoid,
    )
    elim_last_following = _beta_at_term(
        "b",
        "c",
        "S l",
        "u0",
        tag="succ_elim_last_following",
        avoid=elim_last_avoid,
    )
    elim_last = (
        f"exists t u0 h. (({elim_last_current}) /\\ "
        f"(({elim_last_following}) /\\ ({_cell_term('u0', 'h', 't')})))"
    )

    return (
        spec(
            "cell_history_nil",
            history,
            ("add_eq_zero_right", "succ_ne_zero"),
            (
                "split",
                "split",
                "exists 0",
                "norm_num",
                "exists 0",
                "norm_num",
                "split",
                "split",
                "exists 0",
                "norm_num",
                "exists 0",
                "norm_num",
                "intro i",
                "intro hi",
                "exfalso",
                "cases hi",
                "have hsucc : S i = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S i)",
                "apply add_eq_zero_right",
                "exact hi_witness",
                "specialize succ_ne_zero i",
                "apply succ_ne_zero",
                "exact hsucc",
            ),
            "The fixed zero beta code and scale form an exact zero-length "
            "reverse cell history; its edge condition is vacuous.",
        ),
        spec(
            "cell_history_extend",
            "forall b c l t u h. "
            f"({extend_before}) -> ({extend_cell}) -> "
            f"exists b2 c2. ({extend_after})",
            (
                "beta_prefix_extend",
                "finite_lt_succ_eq_or_lt",
                "zero_le",
                "succ_le_succ",
                "le_refl",
            ),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro t",
                "intro u",
                "intro h",
                "intro hhistory",
                "intro hcell",
                "cases hhistory",
                "cases hhistory_right",
                "specialize beta_prefix_extend (S l)",
                "specialize beta_prefix_extend b",
                "specialize beta_prefix_extend c",
                "specialize beta_prefix_extend u",
                "cases beta_prefix_extend",
                "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x",
                "exists x1",
                "split",
                "specialize beta_prefix_extend_witness_witness_right 0",
                "specialize beta_prefix_extend_witness_witness_right 0",
                "apply beta_prefix_extend_witness_witness_right",
                "have hzero : exists gap. gap + 0 = l",
                "specialize zero_le l",
                "exact zero_le",
                "specialize succ_le_succ 0",
                "specialize succ_le_succ l",
                "apply succ_le_succ",
                "exact hzero",
                "exact hhistory_left",
                "split",
                "exact beta_prefix_extend_witness_witness_left",
                "intro i",
                "intro hi",
                "have hsplit : i = l \\/ exists gap. gap + S i = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                "cases hsplit",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exists t",
                "exists u",
                "exists h",
                "split",
                "specialize beta_prefix_extend_witness_witness_right l",
                "specialize beta_prefix_extend_witness_witness_right t",
                "apply beta_prefix_extend_witness_witness_right",
                "specialize le_refl (S l)",
                "exact le_refl",
                "exact hhistory_right_left",
                "split",
                "exact beta_prefix_extend_witness_witness_left",
                "exact hcell",
                f"have hold : {extend_hold}",
                "specialize hhistory_right_right i",
                "apply hhistory_right_right",
                "exact hsplit_right",
                "cases hold",
                "cases hold_witness",
                "cases hold_witness_witness",
                "cases hold_witness_witness_witness",
                "cases hold_witness_witness_witness_right",
                "exists x2",
                "exists x3",
                "exists x4",
                "split",
                "specialize beta_prefix_extend_witness_witness_right i",
                "specialize beta_prefix_extend_witness_witness_right x2",
                "apply beta_prefix_extend_witness_witness_right",
                "exact hi",
                "exact hold_witness_witness_witness_left",
                "split",
                "specialize beta_prefix_extend_witness_witness_right (S i)",
                "specialize beta_prefix_extend_witness_witness_right x3",
                "apply beta_prefix_extend_witness_witness_right",
                "specialize succ_le_succ (S i)",
                "specialize succ_le_succ l",
                "apply succ_le_succ",
                "exact hsplit_right",
                "exact hold_witness_witness_witness_right_left",
                "exact hold_witness_witness_witness_right_right",
            ),
            "Append one exact D06 cell to a reverse beta history while "
            "transporting every old edge.",
        ),
        spec(
            "cell_history_succ_elim",
            "forall b c l u. "
            f"({elim_before}) -> exists t h. "
            f"(({_cell_term('u', 'h', 't')}) /\\ ({elim_after}))",
            ("beta_at_unique", "le_refl", "le_succ"),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro u",
                "intro hhistory",
                "cases hhistory",
                "cases hhistory_right",
                f"have hlast : {elim_last}",
                "specialize hhistory_right_right l",
                "apply hhistory_right_right",
                "specialize le_refl (S l)",
                "exact le_refl",
                "cases hlast",
                "cases hlast_witness",
                "cases hlast_witness_witness",
                "cases hlast_witness_witness_witness",
                "cases hlast_witness_witness_witness_right",
                "have hueq : x1 = u",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique (S l)",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique u",
                "apply beta_at_unique",
                "exact hlast_witness_witness_witness_right_left",
                "exact hhistory_right_left",
                "exists x",
                "exists x2",
                "split",
                "rewrite hueq at hlast_witness_witness_witness_right_right",
                "exact hlast_witness_witness_witness_right_right",
                "split",
                "exact hhistory_left",
                "split",
                "exact hlast_witness_witness_witness_left",
                "intro i",
                "intro hi",
                "specialize hhistory_right_right i",
                "apply hhistory_right_right",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
            ),
            "Expose the final exact D06 cell and reuse the same beta witnesses "
            "for its predecessor history.",
        ),
    )


__all__ = [
    "beta_at",
    "cell_history",
    "cell_list_len",
    "make_ha_cell_history_candidate_theorems",
]
