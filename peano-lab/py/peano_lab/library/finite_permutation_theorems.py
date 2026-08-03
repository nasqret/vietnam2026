"""Isolated constructive entrance lemmas for beta-coded finite permutations.

The helpers in this module are conservative authoring abbreviations only.
They expand boundedness, pointwise injectivity, and pointwise surjectivity into
the unchanged first-order PA language.  No finite-set, function, or
permutation primitive is added to the parser or kernel.

The complete finite pigeonhole theorem is intentionally not declared here.
The checked lemmas isolate its presently available successor branch.  The
other branch has a top value at an interior index and needs one new piece of
coding infrastructure: an extensional beta-code that swaps that index with
the last index (equivalently, deletes and reindexes the interior index), plus
boundedness, injectivity, and occurrence transport for that recoding.  Once
those constructive transport lemmas exist, the same predecessor induction
used below closes the branch; no excluded middle beyond the already checked
bounded/equality decisions is required.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at


_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _identifier(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not (value[0].isalpha() or value[0] == "_")
        or not all(character.isalnum() or character in "_'" for character in value[1:])
        or value in _RESERVED
    ):
        raise ValueError(f"{label} must be a non-reserved Peano identifier")
    return value


def _binders(tag: str, avoid: tuple[str, ...], *stems: str) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"fp_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(avoid):
        raise ValueError("generated finite-permutation binder captures an argument")
    return names


def _lt(left: str, right: str, *, tag: str, avoid: tuple[str, ...]) -> str:
    (gap,) = _binders(tag, avoid, "gap")
    return f"exists {gap}. {gap} + S {left} = {right}"


def bounded_prefix(code: str, scale: str, length: str, *, tag: str) -> str:
    """Expand: every decoded entry at an index below ``length`` is below it."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (code, "code"),
            (scale, "scale"),
            (length, "length"),
        )
    )
    i, value = _binders(tag, variables, "i", "value")
    avoid = variables + (i, value)
    index_bound = _lt(i, length, tag=f"{tag}_index", avoid=avoid)
    entry = beta_at(code, scale, i, value, tag=f"{tag}_entry")
    value_bound = _lt(value, length, tag=f"{tag}_value", avoid=avoid)
    return (
        f"forall {i}. ({index_bound}) -> exists {value}. "
        f"(({entry}) /\\ ({value_bound}))"
    )


def bounded_successor_prefix(
    code: str,
    scale: str,
    predecessor: str,
    *,
    tag: str,
) -> str:
    """Expand boundedness at the audited compound length ``S predecessor``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (code, "code"),
            (scale, "scale"),
            (predecessor, "length predecessor"),
        )
    )
    i, value = _binders(tag, variables, "i", "value")
    avoid = variables + (i, value)
    length_term = f"S {predecessor}"
    index_bound = _lt(i, length_term, tag=f"{tag}_index", avoid=avoid)
    entry = beta_at(code, scale, i, value, tag=f"{tag}_entry")
    value_bound = _lt(value, length_term, tag=f"{tag}_value", avoid=avoid)
    return (
        f"forall {i}. ({index_bound}) -> exists {value}. "
        f"(({entry}) /\\ ({value_bound}))"
    )


def injective_prefix(code: str, scale: str, length: str, *, tag: str) -> str:
    """Expand pointwise injectivity on the decoded prefix."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (code, "code"),
            (scale, "scale"),
            (length, "length"),
        )
    )
    i, j, value = _binders(tag, variables, "i", "j", "value")
    avoid = variables + (i, j, value)
    i_bound = _lt(i, length, tag=f"{tag}_i", avoid=avoid)
    j_bound = _lt(j, length, tag=f"{tag}_j", avoid=avoid)
    left = beta_at(code, scale, i, value, tag=f"{tag}_left")
    right = beta_at(code, scale, j, value, tag=f"{tag}_right")
    return (
        f"forall {i} {j} {value}. ({i_bound}) -> ({j_bound}) -> "
        f"({left}) -> ({right}) -> {i} = {j}"
    )


def injective_successor_prefix(
    code: str,
    scale: str,
    predecessor: str,
    *,
    tag: str,
) -> str:
    """Expand injectivity at the audited compound length ``S predecessor``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (code, "code"),
            (scale, "scale"),
            (predecessor, "length predecessor"),
        )
    )
    i, j, value = _binders(tag, variables, "i", "j", "value")
    avoid = variables + (i, j, value)
    length_term = f"S {predecessor}"
    i_bound = _lt(i, length_term, tag=f"{tag}_i", avoid=avoid)
    j_bound = _lt(j, length_term, tag=f"{tag}_j", avoid=avoid)
    left = beta_at(code, scale, i, value, tag=f"{tag}_left")
    right = beta_at(code, scale, j, value, tag=f"{tag}_right")
    return (
        f"forall {i} {j} {value}. ({i_bound}) -> ({j_bound}) -> "
        f"({left}) -> ({right}) -> {i} = {j}"
    )


def surjective_prefix(code: str, scale: str, length: str, *, tag: str) -> str:
    """Expand pointwise surjectivity onto ``0,...,length-1``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (code, "code"),
            (scale, "scale"),
            (length, "length"),
        )
    )
    value, i = _binders(tag, variables, "value", "i")
    avoid = variables + (value, i)
    value_bound = _lt(value, length, tag=f"{tag}_value", avoid=avoid)
    index_bound = _lt(i, length, tag=f"{tag}_index", avoid=avoid)
    entry = beta_at(code, scale, i, value, tag=f"{tag}_entry")
    return (
        f"forall {value}. ({value_bound}) -> exists {i}. "
        f"(({index_bound}) /\\ ({entry}))"
    )


def surjective_successor_prefix(
    code: str,
    scale: str,
    predecessor: str,
    *,
    tag: str,
) -> str:
    """Expand surjectivity at the audited compound length ``S predecessor``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (code, "code"),
            (scale, "scale"),
            (predecessor, "length predecessor"),
        )
    )
    value, i = _binders(tag, variables, "value", "i")
    avoid = variables + (value, i)
    length_term = f"S {predecessor}"
    value_bound = _lt(value, length_term, tag=f"{tag}_value", avoid=avoid)
    index_bound = _lt(i, length_term, tag=f"{tag}_index", avoid=avoid)
    entry = beta_at(code, scale, i, value, tag=f"{tag}_entry")
    return (
        f"forall {value}. ({value_bound}) -> exists {i}. "
        f"(({index_bound}) /\\ ({entry}))"
    )


def contains_prefix(
    code: str,
    scale: str,
    length: str,
    value: str,
    *,
    tag: str,
) -> str:
    """Expand existence of ``value`` at a decoded position below ``length``."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (code, "code"),
            (scale, "scale"),
            (length, "length"),
            (value, "value"),
        )
    )
    (i,) = _binders(tag, variables, "i")
    avoid = variables + (i,)
    index_bound = _lt(i, length, tag=f"{tag}_index", avoid=avoid)
    entry = beta_at(code, scale, i, value, tag=f"{tag}_entry")
    return f"exists {i}. (({index_bound}) /\\ ({entry}))"


def permutation_prefix(code: str, scale: str, length: str, *, tag: str) -> str:
    """Expand boundedness, injectivity, and surjectivity as one formula."""

    bounded = bounded_prefix(code, scale, length, tag=f"{tag}_bounded")
    injective = injective_prefix(code, scale, length, tag=f"{tag}_injective")
    surjective = surjective_prefix(code, scale, length, tag=f"{tag}_surjective")
    return f"(({bounded}) /\\ (({injective}) /\\ ({surjective})))"


def make_finite_permutation_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the checked portion of the finite-permutation induction gate."""

    surjective_zero = surjective_prefix("b", "c", "n", tag="zero")
    injective_succ = injective_prefix("b", "c", "sn", tag="inj_succ")
    injective_prefix_n = injective_prefix("b", "c", "n", tag="inj_prefix")
    bounded_succ = bounded_prefix("b", "c", "sn", tag="bounded_succ")
    bounded_prefix_n = bounded_prefix("b", "c", "n", tag="bounded_prefix")
    top_entry_i = beta_at("b", "c", "i", "n", tag="top_i")
    last_entry_x = beta_at("b", "c", "n", "x", tag="last_x")
    last_entry_n = beta_at("b", "c", "n", "n", tag="last_n")
    surjective_n = surjective_prefix("b", "c", "n", tag="surj_n")
    surjective_succ = surjective_prefix("b", "c", "sn", tag="surj_succ")
    contains_l_y = contains_prefix("b", "c", "l", "y", tag="contains_l")
    contains_top = contains_prefix("b", "c", "n", "n", tag="contains_top")
    replacement_entry = beta_at("z", "d", "i", "s", tag="replace_entry")
    replacement_old = beta_at("b", "c", "j", "a", tag="replace_old")
    replacement_new = beta_at("z", "d", "j", "a", tag="replace_new")
    swap_old_i = beta_at("b", "c", "i", "x", tag="swap_old_i")
    swap_old_n = beta_at("b", "c", "n", "y", tag="swap_old_n")
    swap_new_i = beta_at("z", "d", "i", "y", tag="swap_new_i")
    swap_new_n = beta_at("z", "d", "n", "x", tag="swap_new_n")
    swap_old_j = beta_at("b", "c", "j", "a", tag="swap_old_j")
    swap_new_j = beta_at("z", "d", "j", "a", tag="swap_new_j")
    swap_exists_old_i = beta_at("b", "c", "i", "x", tag="swap_exists_old_i")
    swap_exists_old_n = beta_at("b", "c", "n", "y", tag="swap_exists_old_n")
    swap_exists_new_i = beta_at("z", "d", "i", "y", tag="swap_exists_new_i")
    swap_exists_new_n = beta_at("z", "d", "n", "x", tag="swap_exists_new_n")
    swap_exists_old_j = beta_at("b", "c", "j", "a", tag="swap_exists_old_j")
    swap_exists_new_j = beta_at("z", "d", "j", "a", tag="swap_exists_new_j")
    reflect_new_i = beta_at("z", "d", "i", "y", tag="reflect_new_i")
    reflect_new_n = beta_at("z", "d", "n", "x", tag="reflect_new_n")
    reflect_old_k = beta_at("b", "c", "k", "v", tag="reflect_old_k")
    reflect_new_k = beta_at("z", "d", "k", "v", tag="reflect_new_k")
    reflect_old_j = beta_at("b", "c", "j", "a", tag="reflect_old_j")
    reflect_new_j = beta_at("z", "d", "j", "a", tag="reflect_new_j")
    bounded_entry_prefix = bounded_prefix("b", "c", "l", tag="entry_bound")
    bounded_entry_at = beta_at("b", "c", "i", "x", tag="entry_bound_at")
    bounded_swap_old = bounded_prefix("b", "c", "sn", tag="swap_bound_old")
    bounded_swap_new = bounded_prefix("z", "d", "sn", tag="swap_bound_new")
    bounded_swap_old_i = beta_at("b", "c", "i", "x", tag="swap_bound_old_i")
    bounded_swap_old_n = beta_at("b", "c", "n", "y", tag="swap_bound_old_n")
    bounded_swap_new_i = beta_at("z", "d", "i", "y", tag="swap_bound_new_i")
    bounded_swap_new_n = beta_at("z", "d", "n", "x", tag="swap_bound_new_n")
    bounded_swap_old_j = beta_at("b", "c", "j", "a", tag="swap_bound_old_j")
    bounded_swap_new_j = beta_at("z", "d", "j", "a", tag="swap_bound_new_j")
    injective_swap_old = injective_prefix("b", "c", "sn", tag="swap_inj_old")
    injective_swap_new = injective_prefix("z", "d", "sn", tag="swap_inj_new")
    injective_swap_old_i = beta_at("b", "c", "i", "x", tag="swap_inj_old_i")
    injective_swap_old_n = beta_at("b", "c", "n", "y", tag="swap_inj_old_n")
    injective_swap_new_i = beta_at("z", "d", "i", "y", tag="swap_inj_new_i")
    injective_swap_new_n = beta_at("z", "d", "n", "x", tag="swap_inj_new_n")
    injective_swap_old_j = beta_at("b", "c", "j", "a", tag="swap_inj_old_j")
    injective_swap_new_j = beta_at("z", "d", "j", "a", tag="swap_inj_new_j")
    surjective_swap_old = surjective_prefix("b", "c", "sn", tag="swap_surj_old")
    surjective_swap_new = surjective_prefix("z", "d", "sn", tag="swap_surj_new")
    surjective_swap_old_i = beta_at("b", "c", "i", "x", tag="swap_surj_old_i")
    surjective_swap_old_n = beta_at("b", "c", "n", "y", tag="swap_surj_old_n")
    surjective_swap_new_i = beta_at("z", "d", "i", "y", tag="swap_surj_new_i")
    surjective_swap_new_n = beta_at("z", "d", "n", "x", tag="swap_surj_new_n")
    surjective_swap_old_j = beta_at("b", "c", "j", "a", tag="swap_surj_old_j")
    surjective_swap_new_j = beta_at("z", "d", "j", "a", tag="swap_surj_new_j")
    reflect_entries_contract = (
        "forall j a. "
        f"(exists h. h + S j = S n) -> ({reflect_new_j}) -> "
        "((j = i /\\ a = y) \\/ ((j = n /\\ a = x) \\/ "
        f"(~(j = i) /\\ (~(j = n) /\\ ({reflect_old_j})))))"
    )
    reflect_contract = (
        "forall b c z d n i x y. "
        f"({reflect_new_i}) -> ({reflect_new_n}) -> "
        "(forall k v. (exists h. h + S k = S n) -> "
        f"~(k = i) -> ~(k = n) -> ({reflect_old_k}) -> "
        f"({reflect_new_k})) -> {reflect_entries_contract}"
    )
    pigeonhole_bounded = bounded_prefix("b", "c", "n", tag="pigeon_bounded")
    pigeonhole_injective = injective_prefix(
        "b", "c", "n", tag="pigeon_injective"
    )
    pigeonhole_surjective = surjective_prefix(
        "b", "c", "n", tag="pigeon_surjective"
    )
    swapped_bounded_succ = bounded_prefix(
        "x2", "x3", "pigeon_sn", tag="pigeon_swapped_bounded"
    ).replace("pigeon_sn", "S n")
    swapped_injective_succ = injective_prefix(
        "x2", "x3", "pigeon_sn", tag="pigeon_swapped_injective"
    ).replace("pigeon_sn", "S n")
    swapped_bounded_prefix = bounded_prefix(
        "x2", "x3", "n", tag="pigeon_swapped_prefix_bounded"
    )
    swapped_injective_prefix = injective_prefix(
        "x2", "x3", "n", tag="pigeon_swapped_prefix_injective"
    )
    swapped_surjective_prefix = surjective_prefix(
        "x2", "x3", "n", tag="pigeon_swapped_prefix_surjective"
    )
    swapped_surjective_succ = surjective_prefix(
        "x2", "x3", "pigeon_sn", tag="pigeon_swapped_surjective"
    ).replace("pigeon_sn", "S n")
    swapped_top_at_j = beta_at("x2", "x3", "j", "n", tag="pigeon_top_j")
    swapped_new_i = beta_at("x2", "x3", "x", "x1", tag="pigeon_new_i")
    swapped_new_n = beta_at("x2", "x3", "n", "n", tag="pigeon_new_n")
    swapped_old_j = beta_at("b", "c", "j", "a", tag="pigeon_old_j")
    swapped_new_j = beta_at("x2", "x3", "j", "a", tag="pigeon_new_j")
    pigeon_swap_old_i = beta_at("b", "c", "x", "n", tag="pigeon_swap_old_i")
    pigeon_swap_old_n = beta_at("b", "c", "n", "x1", tag="pigeon_swap_old_n")
    pigeon_swap_new_i = beta_at("z", "d", "x", "x1", tag="pigeon_swap_new_i")
    pigeon_swap_new_n = beta_at("z", "d", "n", "n", tag="pigeon_swap_new_n")
    pigeon_swap_old_other = beta_at(
        "b", "c", "j", "a", tag="pigeon_swap_old_other"
    )
    pigeon_swap_new_other = beta_at(
        "z", "d", "j", "a", tag="pigeon_swap_new_other"
    )
    pigeon_swap_contract = (
        "exists z d. "
        f"(({pigeon_swap_new_i}) /\\ (({pigeon_swap_new_n}) /\\ "
        "forall j a. (exists h. h + S j = S n) -> "
        f"~(j = x) -> ~(j = n) -> ({pigeon_swap_old_other}) -> "
        f"({pigeon_swap_new_other})))"
    )

    return (
        spec(
            "finite_surjective_zero",
            f"forall b c n. n = 0 -> ({surjective_zero})",
            ("add_eq_zero_right", "succ_ne_zero"),
            (
                "intro b",
                "intro c",
                "intro n",
                "intro hn",
                "intro y",
                "intro hy",
                "rewrite hn at hy",
                "exfalso",
                "cases hy",
                "have hsy : S y = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S y)",
                "apply add_eq_zero_right",
                "exact hy_witness",
                "specialize succ_ne_zero y",
                "apply succ_ne_zero",
                "exact hsy",
            ),
            "The empty decoded prefix is surjective onto the empty interval.",
        ),
        spec(
            "finite_injective_prefix_succ",
            f"forall b c n sn. sn = S n -> ({injective_succ}) -> "
            f"({injective_prefix_n})",
            ("le_succ",),
            (
                "intro b",
                "intro c",
                "intro n",
                "intro sn",
                "intro hsn",
                "intro hinj",
                "rewrite hsn at hinj",
                "rewrite hsn at hinj",
                "intro i",
                "intro j",
                "intro x",
                "intro hi",
                "intro hj",
                "intro hxi",
                "intro hxj",
                "specialize hinj i",
                "specialize hinj j",
                "specialize hinj x",
                "apply hinj",
                "specialize le_succ (S i)",
                "specialize le_succ n",
                "apply le_succ",
                "exact hi",
                "specialize le_succ (S j)",
                "specialize le_succ n",
                "apply le_succ",
                "exact hj",
                "exact hxi",
                "exact hxj",
            ),
            "Injectivity of a successor prefix restricts to its old prefix.",
        ),
        spec(
            "finite_lt_succ_eq_or_lt",
            "forall n x. (exists h. h + S x = S n) -> "
            "x = n \\/ exists h. h + S x = n",
            ("le_of_succ_le_succ", "le_eq_or_lt"),
            (
                "intro n",
                "intro x",
                "intro hlt",
                "have hle : exists h. h + x = n",
                "specialize le_of_succ_le_succ x",
                "specialize le_of_succ_le_succ n",
                "apply le_of_succ_le_succ",
                "exact hlt",
                "specialize le_eq_or_lt x",
                "specialize le_eq_or_lt n",
                "apply le_eq_or_lt",
                "exact hle",
            ),
            "A value below a successor is the predecessor or lies below it.",
        ),
        spec(
            "finite_bounded_entry_lt",
            f"forall b c l i x. ({bounded_entry_prefix}) -> "
            f"(exists h. h + S i = l) -> ({bounded_entry_at}) -> "
            "exists h. h + S x = l",
            ("beta_at_unique",),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro i",
                "intro x",
                "intro hbounded",
                "intro hi",
                "intro hentry",
                "specialize hbounded i",
                "have hdecoded : exists a. "
                "(((exists h. h + S a = S ((S i) * c)) /\\ "
                "exists q. b = q * S ((S i) * c) + a) /\\ "
                "exists h. h + S a = l)",
                "apply hbounded",
                "exact hi",
                "cases hdecoded",
                "cases hdecoded_witness",
                "have hxa : x = x1",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique i",
                "specialize beta_at_unique x",
                "specialize beta_at_unique x1",
                "apply beta_at_unique",
                "exact hentry",
                "exact hdecoded_witness_left",
                "rewrite hxa",
                "exact hdecoded_witness_right",
            ),
            "Every explicitly decoded entry of a bounded prefix satisfies its value bound.",
        ),
        spec(
            "beta_prefix_replace_exists",
            "forall b c i s k. (exists h. h + S i = k) -> exists z d. "
            f"(({replacement_entry}) /\\ forall j a. "
            "(exists h. h + S j = k) -> ~(j = i) -> "
            f"({replacement_old}) -> ({replacement_new}))",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "finite_lt_succ_eq_or_lt",
                "beta_prefix_extend",
                "beta_at_exists",
                "beta_at_unique",
            ),
            (
                "intro b",
                "intro c",
                "intro i",
                "intro s",
                "induction k",
                "intro hi",
                "exfalso",
                "cases hi",
                "have hsi : S i = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S i)",
                "apply add_eq_zero_right",
                "exact hi_witness",
                "specialize succ_ne_zero i",
                "apply succ_ne_zero",
                "exact hsi",
                "intro hi",
                "have hisplit : i = k \\/ exists h. h + S i = k",
                "specialize finite_lt_succ_eq_or_lt k",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                "cases hisplit",
                "specialize beta_prefix_extend k",
                "specialize beta_prefix_extend b",
                "specialize beta_prefix_extend c",
                "specialize beta_prefix_extend s",
                "cases beta_prefix_extend",
                "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x",
                "exists x1",
                "split",
                "rewrite hisplit_left",
                "rewrite hisplit_left",
                "exact beta_prefix_extend_witness_witness_left",
                "intro j",
                "intro a",
                "intro hj",
                "intro hji",
                "intro hold",
                "have hjsplit : j = k \\/ exists h. h + S j = k",
                "specialize finite_lt_succ_eq_or_lt k",
                "specialize finite_lt_succ_eq_or_lt j",
                "apply finite_lt_succ_eq_or_lt",
                "exact hj",
                "cases hjsplit",
                "exfalso",
                "apply hji",
                "trans k",
                "exact hjsplit_left",
                "symm",
                "exact hisplit_left",
                "specialize beta_prefix_extend_witness_witness_right j",
                "specialize beta_prefix_extend_witness_witness_right a",
                "apply beta_prefix_extend_witness_witness_right",
                "exact hjsplit_right",
                "exact hold",
                "have hreplaced : exists z d. "
                "(((exists h. h + S s = S ((S i) * d)) /\\ "
                "exists q. z = q * S ((S i) * d) + s) /\\ "
                "forall j a. (exists h. h + S j = k) -> ~(j = i) -> "
                "((exists h. h + S a = S ((S j) * c)) /\\ "
                "exists q. b = q * S ((S j) * c) + a) -> "
                "((exists h. h + S a = S ((S j) * d)) /\\ "
                "exists q. z = q * S ((S j) * d) + a))",
                "apply IH",
                "exact hisplit_right",
                "cases hreplaced",
                "cases hreplaced_witness",
                "cases hreplaced_witness_witness",
                "specialize beta_at_exists b",
                "specialize beta_at_exists c",
                "specialize beta_at_exists k",
                "cases beta_at_exists",
                "specialize beta_prefix_extend k",
                "specialize beta_prefix_extend x",
                "specialize beta_prefix_extend x1",
                "specialize beta_prefix_extend x2",
                "cases beta_prefix_extend",
                "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x3",
                "exists x4",
                "split",
                "specialize beta_prefix_extend_witness_witness_right i",
                "specialize beta_prefix_extend_witness_witness_right s",
                "apply beta_prefix_extend_witness_witness_right",
                "exact hisplit_right",
                "exact hreplaced_witness_witness_left",
                "intro j",
                "intro a",
                "intro hj",
                "intro hji",
                "intro hold",
                "have hjsplit : j = k \\/ exists h. h + S j = k",
                "specialize finite_lt_succ_eq_or_lt k",
                "specialize finite_lt_succ_eq_or_lt j",
                "apply finite_lt_succ_eq_or_lt",
                "exact hj",
                "cases hjsplit",
                "have hax : a = x2",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique k",
                "specialize beta_at_unique a",
                "specialize beta_at_unique x2",
                "apply beta_at_unique",
                "rewrite hjsplit_left at hold",
                "rewrite hjsplit_left at hold",
                "exact hold",
                "exact beta_at_exists_witness",
                "rewrite hjsplit_left",
                "rewrite hjsplit_left",
                "rewrite hax",
                "rewrite hax",
                "exact beta_prefix_extend_witness_witness_left",
                "have hmiddle : ((exists h. h + S a = S ((S j) * x1)) /\\ "
                "exists q. x = q * S ((S j) * x1) + a)",
                "specialize hreplaced_witness_witness_right j",
                "specialize hreplaced_witness_witness_right a",
                "apply hreplaced_witness_witness_right",
                "exact hjsplit_right",
                "exact hji",
                "exact hold",
                "specialize beta_prefix_extend_witness_witness_right j",
                "specialize beta_prefix_extend_witness_witness_right a",
                "apply beta_prefix_extend_witness_witness_right",
                "exact hjsplit_right",
                "exact hmiddle",
            ),
            "Recode a finite beta prefix while replacing one interior entry.",
        ),
        spec(
            "beta_prefix_swap_last_from_entries",
            "forall b c n i x y. (exists h. h + S i = n) -> "
            f"({swap_old_i}) -> ({swap_old_n}) -> exists z d. "
            f"(({swap_new_i}) /\\ (({swap_new_n}) /\\ forall j a. "
            "(exists h. h + S j = S n) -> ~(j = i) -> ~(j = n) -> "
            f"({swap_old_j}) -> ({swap_new_j})))",
            (
                "beta_prefix_replace_exists",
                "le_succ",
                "le_refl",
                "lt_irrefl_expanded",
            ),
            (
                "intro b",
                "intro c",
                "intro n",
                "intro i",
                "intro x",
                "intro y",
                "intro hi",
                "intro hxi",
                "intro hyn",
                "have hisn : exists h. h + S i = S n",
                "specialize le_succ (S i)",
                "specialize le_succ n",
                "apply le_succ",
                "exact hi",
                "have hnsn : exists h. h + S n = S n",
                "specialize le_refl (S n)",
                "exact le_refl",
                "have hin : ~(i = n)",
                "intro hin_eq",
                "specialize lt_irrefl_expanded n",
                "apply lt_irrefl_expanded",
                "rewrite hin_eq at hi",
                "exact hi",
                "have hni : ~(n = i)",
                "intro hni_eq",
                "apply hin",
                "symm",
                "exact hni_eq",
                "have hfirst : exists z d. "
                "(((exists h. h + S y = S ((S i) * d)) /\\ "
                "exists q. z = q * S ((S i) * d) + y) /\\ "
                "forall j a. (exists h. h + S j = S n) -> ~(j = i) -> "
                "((exists h. h + S a = S ((S j) * c)) /\\ "
                "exists q. b = q * S ((S j) * c) + a) -> "
                "((exists h. h + S a = S ((S j) * d)) /\\ "
                "exists q. z = q * S ((S j) * d) + a))",
                "specialize beta_prefix_replace_exists b",
                "specialize beta_prefix_replace_exists c",
                "specialize beta_prefix_replace_exists i",
                "specialize beta_prefix_replace_exists y",
                "specialize beta_prefix_replace_exists (S n)",
                "apply beta_prefix_replace_exists",
                "exact hisn",
                "cases hfirst",
                "cases hfirst_witness",
                "cases hfirst_witness_witness",
                "have hfirst_n : ((exists h. h + S y = S ((S n) * x2)) /\\ "
                "exists q. x1 = q * S ((S n) * x2) + y)",
                "specialize hfirst_witness_witness_right n",
                "specialize hfirst_witness_witness_right y",
                "apply hfirst_witness_witness_right",
                "exact hnsn",
                "exact hni",
                "exact hyn",
                "have hsecond : exists z d. "
                "(((exists h. h + S x = S ((S n) * d)) /\\ "
                "exists q. z = q * S ((S n) * d) + x) /\\ "
                "forall j a. (exists h. h + S j = S n) -> ~(j = n) -> "
                "((exists h. h + S a = S ((S j) * x2)) /\\ "
                "exists q. x1 = q * S ((S j) * x2) + a) -> "
                "((exists h. h + S a = S ((S j) * d)) /\\ "
                "exists q. z = q * S ((S j) * d) + a))",
                "specialize beta_prefix_replace_exists x1",
                "specialize beta_prefix_replace_exists x2",
                "specialize beta_prefix_replace_exists n",
                "specialize beta_prefix_replace_exists x",
                "specialize beta_prefix_replace_exists (S n)",
                "apply beta_prefix_replace_exists",
                "exact hnsn",
                "cases hsecond",
                "cases hsecond_witness",
                "cases hsecond_witness_witness",
                "exists x3",
                "exists x4",
                "split",
                "specialize hsecond_witness_witness_right i",
                "specialize hsecond_witness_witness_right y",
                "apply hsecond_witness_witness_right",
                "exact hisn",
                "exact hin",
                "exact hfirst_witness_witness_left",
                "split",
                "exact hsecond_witness_witness_left",
                "intro j",
                "intro a",
                "intro hj",
                "intro hji",
                "intro hjn",
                "intro hold",
                "have hmiddle : ((exists h. h + S a = S ((S j) * x2)) /\\ "
                "exists q. x1 = q * S ((S j) * x2) + a)",
                "specialize hfirst_witness_witness_right j",
                "specialize hfirst_witness_witness_right a",
                "apply hfirst_witness_witness_right",
                "exact hj",
                "exact hji",
                "exact hold",
                "specialize hsecond_witness_witness_right j",
                "specialize hsecond_witness_witness_right a",
                "apply hsecond_witness_witness_right",
                "exact hj",
                "exact hjn",
                "exact hmiddle",
            ),
            "Swap a chosen interior beta entry with the last entry, given both decoded values.",
        ),
        spec(
            "beta_prefix_swap_last_exists",
            "forall b c n i. (exists h. h + S i = n) -> "
            f"exists z d x y. (({swap_exists_old_i}) /\\ "
            f"(({swap_exists_old_n}) /\\ (({swap_exists_new_i}) /\\ "
            f"(({swap_exists_new_n}) /\\ forall j a. "
            "(exists h. h + S j = S n) -> ~(j = i) -> ~(j = n) -> "
            f"({swap_exists_old_j}) -> ({swap_exists_new_j})))))",
            ("beta_at_exists", "beta_prefix_swap_last_from_entries"),
            (
                "intro b",
                "intro c",
                "intro n",
                "intro i",
                "intro hi",
                "have hdecode_i : forall u v k. exists a. "
                "((exists h. h + S a = S ((S k) * v)) /\\ "
                "exists q. u = q * S ((S k) * v) + a)",
                "exact beta_at_exists",
                "have hdecode_n : forall u v k. exists a. "
                "((exists h. h + S a = S ((S k) * v)) /\\ "
                "exists q. u = q * S ((S k) * v) + a)",
                "exact beta_at_exists",
                "specialize hdecode_i b",
                "specialize hdecode_i c",
                "specialize hdecode_i i",
                "cases hdecode_i",
                "specialize hdecode_n b",
                "specialize hdecode_n c",
                "specialize hdecode_n n",
                "cases hdecode_n",
                "have hswap : exists z d. "
                "(((exists h. h + S x1 = S ((S i) * d)) /\\ "
                "exists q. z = q * S ((S i) * d) + x1) /\\ "
                "(((exists h. h + S x = S ((S n) * d)) /\\ "
                "exists q. z = q * S ((S n) * d) + x) /\\ "
                "forall j a. (exists h. h + S j = S n) -> "
                "~(j = i) -> ~(j = n) -> "
                "((exists h. h + S a = S ((S j) * c)) /\\ "
                "exists q. b = q * S ((S j) * c) + a) -> "
                "((exists h. h + S a = S ((S j) * d)) /\\ "
                "exists q. z = q * S ((S j) * d) + a)))",
                "specialize beta_prefix_swap_last_from_entries b",
                "specialize beta_prefix_swap_last_from_entries c",
                "specialize beta_prefix_swap_last_from_entries n",
                "specialize beta_prefix_swap_last_from_entries i",
                "specialize beta_prefix_swap_last_from_entries x",
                "specialize beta_prefix_swap_last_from_entries x1",
                "apply beta_prefix_swap_last_from_entries",
                "exact hi",
                "exact hdecode_i_witness",
                "exact hdecode_n_witness",
                "cases hswap",
                "cases hswap_witness",
                "exists x2",
                "exists x3",
                "exists x",
                "exists x1",
                "split",
                "exact hdecode_i_witness",
                "split",
                "exact hdecode_n_witness",
                "exact hswap_witness_witness",
            ),
            "Construct an extensional beta code with an interior entry swapped with the last.",
        ),
        spec(
            "beta_prefix_swap_last_reflect",
            reflect_contract,
            ("eq_decidable", "beta_at_exists", "beta_at_unique"),
            (
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro n",
                "intro i",
                "intro x",
                "intro y",
                "intro hnew_i",
                "intro hnew_n",
                "intro hpreserve",
                "intro j",
                "intro a",
                "intro hj",
                "intro hnew",
                "specialize eq_decidable j",
                "specialize eq_decidable i",
                "cases eq_decidable",
                "left",
                "split",
                "exact eq_decidable_left",
                "specialize beta_at_unique z",
                "specialize beta_at_unique d",
                "specialize beta_at_unique i",
                "specialize beta_at_unique a",
                "specialize beta_at_unique y",
                "apply beta_at_unique",
                "rewrite eq_decidable_left at hnew",
                "rewrite eq_decidable_left at hnew",
                "exact hnew",
                "exact hnew_i",
                "specialize eq_decidable_before2 n",
                "cases eq_decidable_before2",
                "right",
                "left",
                "split",
                "exact eq_decidable_before2_left",
                "specialize beta_at_unique z",
                "specialize beta_at_unique d",
                "specialize beta_at_unique n",
                "specialize beta_at_unique a",
                "specialize beta_at_unique x",
                "apply beta_at_unique",
                "rewrite eq_decidable_before2_left at hnew",
                "rewrite eq_decidable_before2_left at hnew",
                "exact hnew",
                "exact hnew_n",
                "specialize beta_at_exists b",
                "specialize beta_at_exists c",
                "specialize beta_at_exists j",
                "cases beta_at_exists",
                "have htransport : ((exists h. h + S x1 = S ((S j) * d)) /\\ "
                "exists q. z = q * S ((S j) * d) + x1)",
                "specialize hpreserve j",
                "specialize hpreserve x1",
                "apply hpreserve",
                "exact hj",
                "exact eq_decidable_right",
                "exact eq_decidable_before2_right",
                "exact beta_at_exists_witness",
                "have hav : a = x1",
                "specialize beta_at_unique z",
                "specialize beta_at_unique d",
                "specialize beta_at_unique j",
                "specialize beta_at_unique a",
                "specialize beta_at_unique x1",
                "apply beta_at_unique",
                "exact hnew",
                "exact htransport",
                "right",
                "right",
                "split",
                "exact eq_decidable_right",
                "split",
                "exact eq_decidable_before2_right",
                "rewrite hav",
                "rewrite hav",
                "exact beta_at_exists_witness",
            ),
            "Every decoded swapped entry reflects to one of the two moved entries or the original index.",
        ),
        spec(
            "finite_swap_last_bounded",
            f"forall b c z d n sn i x y. sn = S n -> "
            f"(exists h. h + S i = n) -> ({bounded_swap_old}) -> "
            f"({bounded_swap_old_i}) -> ({bounded_swap_old_n}) -> "
            f"({bounded_swap_new_i}) -> ({bounded_swap_new_n}) -> "
            "(forall j a. (exists h. h + S j = S n) -> "
            f"~(j = i) -> ~(j = n) -> ({bounded_swap_old_j}) -> "
            f"({bounded_swap_new_j})) -> ({bounded_swap_new})",
            (
                "finite_bounded_entry_lt",
                "eq_decidable",
                "le_succ",
                "le_refl",
            ),
            (
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro n",
                "intro sn",
                "intro i",
                "intro x",
                "intro y",
                "intro hsn",
                "intro hi",
                "intro hbounded",
                "intro hold_i",
                "intro hold_n",
                "intro hnew_i",
                "intro hnew_n",
                "intro hpreserve",
                "rewrite hsn at hbounded",
                "rewrite hsn at hbounded",
                "have hisn : exists h. h + S i = S n",
                "specialize le_succ (S i)",
                "specialize le_succ n",
                "apply le_succ",
                "exact hi",
                "have hnsn : exists h. h + S n = S n",
                "specialize le_refl (S n)",
                "exact le_refl",
                f"have hentry_bound_i : forall b c l i x. "
                f"({bounded_entry_prefix}) -> (exists h. h + S i = l) -> "
                f"({bounded_entry_at}) -> exists h. h + S x = l",
                "exact finite_bounded_entry_lt",
                f"have hentry_bound_n : forall b c l i x. "
                f"({bounded_entry_prefix}) -> (exists h. h + S i = l) -> "
                f"({bounded_entry_at}) -> exists h. h + S x = l",
                "exact finite_bounded_entry_lt",
                "have hxb : exists h. h + S x = S n",
                "specialize hentry_bound_i b",
                "specialize hentry_bound_i c",
                "specialize hentry_bound_i (S n)",
                "specialize hentry_bound_i i",
                "specialize hentry_bound_i x",
                "apply hentry_bound_i",
                "exact hbounded",
                "exact hisn",
                "exact hold_i",
                "have hyb : exists h. h + S y = S n",
                "specialize hentry_bound_n b",
                "specialize hentry_bound_n c",
                "specialize hentry_bound_n (S n)",
                "specialize hentry_bound_n n",
                "specialize hentry_bound_n y",
                "apply hentry_bound_n",
                "exact hbounded",
                "exact hnsn",
                "exact hold_n",
                "have heq_i : forall u v. u = v \\/ ~(u = v)",
                "exact eq_decidable",
                "have heq_n : forall u v. u = v \\/ ~(u = v)",
                "exact eq_decidable",
                "rewrite hsn",
                "rewrite hsn",
                "intro j",
                "intro hj",
                "specialize heq_i j",
                "specialize heq_i i",
                "cases heq_i",
                "exists y",
                "split",
                "rewrite heq_i_left",
                "rewrite heq_i_left",
                "exact hnew_i",
                "exact hyb",
                "specialize heq_n j",
                "specialize heq_n n",
                "cases heq_n",
                "exists x",
                "split",
                "rewrite heq_n_left",
                "rewrite heq_n_left",
                "exact hnew_n",
                "exact hxb",
                "specialize hbounded j",
                "have hold : exists a. "
                "(((exists h. h + S a = S ((S j) * c)) /\\ "
                "exists q. b = q * S ((S j) * c) + a) /\\ "
                "exists h. h + S a = S n)",
                "apply hbounded",
                "exact hj",
                "cases hold",
                "cases hold_witness",
                "exists x1",
                "split",
                "specialize hpreserve j",
                "specialize hpreserve x1",
                "apply hpreserve",
                "exact hj",
                "exact heq_i_right",
                "exact heq_n_right",
                "exact hold_witness_left",
                "exact hold_witness_right",
            ),
            "A swap-last recoding preserves boundedness of the full successor prefix.",
        ),
        spec(
            "finite_swap_last_injective",
            f"forall b c z d n sn i x y. sn = S n -> "
            f"(exists h. h + S i = n) -> ({injective_swap_old}) -> "
            f"({injective_swap_old_i}) -> ({injective_swap_old_n}) -> "
            f"({injective_swap_new_i}) -> ({injective_swap_new_n}) -> "
            "(forall j a. (exists h. h + S j = S n) -> "
            f"~(j = i) -> ~(j = n) -> ({injective_swap_old_j}) -> "
            f"({injective_swap_new_j})) -> ({injective_swap_new})",
            ("beta_prefix_swap_last_reflect", "le_succ", "le_refl"),
            (
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro n",
                "intro sn",
                "intro i",
                "intro x",
                "intro y",
                "intro hsn",
                "intro hi",
                "intro hinjective",
                "intro hold_i",
                "intro hold_n",
                "intro hnew_i",
                "intro hnew_n",
                "intro hpreserve",
                "rewrite hsn at hinjective",
                "rewrite hsn at hinjective",
                "have hisn : exists h. h + S i = S n",
                "specialize le_succ (S i)",
                "specialize le_succ n",
                "apply le_succ",
                "exact hi",
                "have hnsn : exists h. h + S n = S n",
                "specialize le_refl (S n)",
                "exact le_refl",
                f"have hreflect_j : {reflect_contract}",
                "exact beta_prefix_swap_last_reflect",
                f"have hreflect_k : {reflect_contract}",
                "exact beta_prefix_swap_last_reflect",
                "rewrite hsn",
                "rewrite hsn",
                "intro j",
                "intro k",
                "intro a",
                "intro hj",
                "intro hk",
                "intro hnew_j",
                "intro hnew_k",
                "specialize hreflect_j b",
                "specialize hreflect_j c",
                "specialize hreflect_j z",
                "specialize hreflect_j d",
                "specialize hreflect_j n",
                "specialize hreflect_j i",
                "specialize hreflect_j x",
                "specialize hreflect_j y",
                f"have hreflect_entries_j : {reflect_entries_contract}",
                "apply hreflect_j",
                "exact hnew_i",
                "exact hnew_n",
                "exact hpreserve",
                "specialize hreflect_entries_j j",
                "specialize hreflect_entries_j a",
                "have hclass_j : ((j = i /\\ a = y) \\/ "
                "((j = n /\\ a = x) \\/ (~(j = i) /\\ "
                "(~(j = n) /\\ ((exists h. h + S a = S ((S j) * c)) /\\ "
                "exists q. b = q * S ((S j) * c) + a)))))",
                "apply hreflect_entries_j",
                "exact hj",
                "exact hnew_j",
                "specialize hreflect_k b",
                "specialize hreflect_k c",
                "specialize hreflect_k z",
                "specialize hreflect_k d",
                "specialize hreflect_k n",
                "specialize hreflect_k i",
                "specialize hreflect_k x",
                "specialize hreflect_k y",
                f"have hreflect_entries_k : {reflect_entries_contract}",
                "apply hreflect_k",
                "exact hnew_i",
                "exact hnew_n",
                "exact hpreserve",
                "specialize hreflect_entries_k k",
                "specialize hreflect_entries_k a",
                "have hclass_k : ((k = i /\\ a = y) \\/ "
                "((k = n /\\ a = x) \\/ (~(k = i) /\\ "
                "(~(k = n) /\\ ((exists h. h + S a = S ((S k) * c)) /\\ "
                "exists q. b = q * S ((S k) * c) + a)))))",
                "apply hreflect_entries_k",
                "exact hk",
                "exact hnew_k",
                "cases hclass_j",
                "cases hclass_j_left",
                "cases hclass_k",
                "cases hclass_k_left",
                "trans i",
                "exact hclass_j_left_left",
                "symm",
                "exact hclass_k_left_left",
                "cases hclass_k_right",
                "cases hclass_k_right_left",
                "have hxy : x = y",
                "trans a",
                "symm",
                "exact hclass_k_right_left_right",
                "exact hclass_j_left_right",
                "have hin : i = n",
                "specialize hinjective i",
                "specialize hinjective n",
                "specialize hinjective x",
                "apply hinjective",
                "exact hisn",
                "exact hnsn",
                "exact hold_i",
                "rewrite hxy",
                "rewrite hxy",
                "exact hold_n",
                "trans i",
                "exact hclass_j_left_left",
                "trans n",
                "exact hin",
                "symm",
                "exact hclass_k_right_left_left",
                "cases hclass_k_right_right",
                "cases hclass_k_right_right_right",
                "have hnk : n = k",
                "specialize hinjective n",
                "specialize hinjective k",
                "specialize hinjective y",
                "apply hinjective",
                "exact hnsn",
                "exact hk",
                "exact hold_n",
                "rewrite <- hclass_j_left_right",
                "rewrite <- hclass_j_left_right",
                "exact hclass_k_right_right_right_right",
                "exfalso",
                "apply hclass_k_right_right_right_left",
                "symm",
                "exact hnk",
                "cases hclass_j_right",
                "cases hclass_j_right_left",
                "cases hclass_k",
                "cases hclass_k_left",
                "have hxy2 : x = y",
                "trans a",
                "symm",
                "exact hclass_j_right_left_right",
                "exact hclass_k_left_right",
                "have hin2 : n = i",
                "specialize hinjective n",
                "specialize hinjective i",
                "specialize hinjective y",
                "apply hinjective",
                "exact hnsn",
                "exact hisn",
                "exact hold_n",
                "rewrite <- hxy2",
                "rewrite <- hxy2",
                "exact hold_i",
                "trans n",
                "exact hclass_j_right_left_left",
                "trans i",
                "exact hin2",
                "symm",
                "exact hclass_k_left_left",
                "cases hclass_k_right",
                "cases hclass_k_right_left",
                "trans n",
                "exact hclass_j_right_left_left",
                "symm",
                "exact hclass_k_right_left_left",
                "cases hclass_k_right_right",
                "cases hclass_k_right_right_right",
                "have hik : i = k",
                "specialize hinjective i",
                "specialize hinjective k",
                "specialize hinjective x",
                "apply hinjective",
                "exact hisn",
                "exact hk",
                "exact hold_i",
                "rewrite <- hclass_j_right_left_right",
                "rewrite <- hclass_j_right_left_right",
                "exact hclass_k_right_right_right_right",
                "exfalso",
                "apply hclass_k_right_right_left",
                "symm",
                "exact hik",
                "cases hclass_j_right_right",
                "cases hclass_j_right_right_right",
                "cases hclass_k",
                "cases hclass_k_left",
                "have hjn : j = n",
                "specialize hinjective j",
                "specialize hinjective n",
                "specialize hinjective y",
                "apply hinjective",
                "exact hj",
                "exact hnsn",
                "rewrite <- hclass_k_left_right",
                "rewrite <- hclass_k_left_right",
                "exact hclass_j_right_right_right_right",
                "exact hold_n",
                "exfalso",
                "apply hclass_j_right_right_right_left",
                "exact hjn",
                "cases hclass_k_right",
                "cases hclass_k_right_left",
                "have hji : j = i",
                "specialize hinjective j",
                "specialize hinjective i",
                "specialize hinjective x",
                "apply hinjective",
                "exact hj",
                "exact hisn",
                "rewrite <- hclass_k_right_left_right",
                "rewrite <- hclass_k_right_left_right",
                "exact hclass_j_right_right_right_right",
                "exact hold_i",
                "exfalso",
                "apply hclass_j_right_right_left",
                "exact hji",
                "cases hclass_k_right_right",
                "cases hclass_k_right_right_right",
                "specialize hinjective j",
                "specialize hinjective k",
                "specialize hinjective a",
                "apply hinjective",
                "exact hj",
                "exact hk",
                "exact hclass_j_right_right_right_right",
                "exact hclass_k_right_right_right_right",
            ),
            "A swap-last recoding preserves injectivity of the full successor prefix.",
        ),
        spec(
            "finite_swap_last_surjective_back",
            f"forall b c z d n sn i x y. sn = S n -> "
            f"(exists h. h + S i = n) -> ({surjective_swap_old_i}) -> "
            f"({surjective_swap_old_n}) -> ({surjective_swap_new_i}) -> "
            f"({surjective_swap_new_n}) -> "
            "(forall j a. (exists h. h + S j = S n) -> "
            f"~(j = i) -> ~(j = n) -> ({surjective_swap_old_j}) -> "
            f"({surjective_swap_new_j})) -> ({surjective_swap_new}) -> "
            f"({surjective_swap_old})",
            ("beta_prefix_swap_last_reflect", "le_succ", "le_refl"),
            (
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro n",
                "intro sn",
                "intro i",
                "intro x",
                "intro y",
                "intro hsn",
                "intro hi",
                "intro hold_i",
                "intro hold_n",
                "intro hnew_i",
                "intro hnew_n",
                "intro hpreserve",
                "intro hsurjective",
                "rewrite hsn at hsurjective",
                "rewrite hsn at hsurjective",
                "have hisn : exists h. h + S i = S n",
                "specialize le_succ (S i)",
                "specialize le_succ n",
                "apply le_succ",
                "exact hi",
                "have hnsn : exists h. h + S n = S n",
                "specialize le_refl (S n)",
                "exact le_refl",
                f"have hreflect : {reflect_contract}",
                "exact beta_prefix_swap_last_reflect",
                "specialize hreflect b",
                "specialize hreflect c",
                "specialize hreflect z",
                "specialize hreflect d",
                "specialize hreflect n",
                "specialize hreflect i",
                "specialize hreflect x",
                "specialize hreflect y",
                "have hreflect_entries : forall j a. "
                "(exists h. h + S j = S n) -> "
                "((exists h. h + S a = S ((S j) * d)) /\\ "
                "exists q. z = q * S ((S j) * d) + a) -> "
                "((j = i /\\ a = y) \\/ ((j = n /\\ a = x) \\/ "
                "(~(j = i) /\\ (~(j = n) /\\ "
                "((exists h. h + S a = S ((S j) * c)) /\\ "
                "exists q. b = q * S ((S j) * c) + a)))))",
                "apply hreflect",
                "exact hnew_i",
                "exact hnew_n",
                "exact hpreserve",
                "rewrite hsn",
                "rewrite hsn",
                "intro a",
                "intro ha",
                "specialize hsurjective a",
                "have hoccurs : exists j. "
                "((exists h. h + S j = S n) /\\ "
                "((exists h. h + S a = S ((S j) * d)) /\\ "
                "exists q. z = q * S ((S j) * d) + a))",
                "apply hsurjective",
                "exact ha",
                "cases hoccurs",
                "cases hoccurs_witness",
                "specialize hreflect_entries x1",
                "specialize hreflect_entries a",
                "have hsource : ((x1 = i /\\ a = y) \\/ "
                "((x1 = n /\\ a = x) \\/ (~(x1 = i) /\\ "
                "(~(x1 = n) /\\ ((exists h. h + S a = S ((S x1) * c)) /\\ "
                "exists q. b = q * S ((S x1) * c) + a)))))",
                "apply hreflect_entries",
                "exact hoccurs_witness_left",
                "exact hoccurs_witness_right",
                "cases hsource",
                "cases hsource_left",
                "exists n",
                "split",
                "exact hnsn",
                "rewrite hsource_left_right",
                "rewrite hsource_left_right",
                "exact hold_n",
                "cases hsource_right",
                "cases hsource_right_left",
                "exists i",
                "split",
                "exact hisn",
                "rewrite hsource_right_left_right",
                "rewrite hsource_right_left_right",
                "exact hold_i",
                "cases hsource_right_right",
                "cases hsource_right_right_right",
                "exists x1",
                "split",
                "exact hoccurs_witness_left",
                "exact hsource_right_right_right_right",
            ),
            "Surjectivity of a swapped successor prefix transports back to the original code.",
        ),
        spec(
            "finite_contains_decidable",
            f"forall b c l y. (({contains_l_y}) \\/ ~({contains_l_y}))",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "finite_lt_succ_eq_or_lt",
                "beta_at_exists",
                "beta_at_unique",
                "eq_decidable",
                "le_refl",
                "le_succ",
            ),
            (
                "intro b",
                "intro c",
                "induction l",
                "intro y",
                "right",
                "intro hcontains",
                "cases hcontains",
                "cases hcontains_witness",
                "cases hcontains_witness_left",
                "have hsi : S x = 0",
                "specialize add_eq_zero_right x1",
                "specialize add_eq_zero_right (S x)",
                "apply add_eq_zero_right",
                "exact hcontains_witness_left_witness",
                "specialize succ_ne_zero x",
                "apply succ_ne_zero",
                "exact hsi",
                "intro y",
                "have hpresent : (exists i. "
                "((exists h. h + S i = l) /\\ "
                "((exists h. h + S y = S ((S i) * c)) /\\ "
                "exists q. b = q * S ((S i) * c) + y))) \\/ "
                "~(exists i. ((exists h. h + S i = l) /\\ "
                "((exists h. h + S y = S ((S i) * c)) /\\ "
                "exists q. b = q * S ((S i) * c) + y)))",
                "specialize IH y",
                "exact IH",
                "cases hpresent",
                "left",
                "cases hpresent_left",
                "cases hpresent_left_witness",
                "exists x",
                "split",
                "specialize le_succ (S x)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hpresent_left_witness_left",
                "exact hpresent_left_witness_right",
                "specialize beta_at_exists b",
                "specialize beta_at_exists c",
                "specialize beta_at_exists l",
                "cases beta_at_exists",
                "specialize eq_decidable x",
                "specialize eq_decidable y",
                "cases eq_decidable",
                "left",
                "exists l",
                "split",
                "specialize le_refl (S l)",
                "exact le_refl",
                "rewrite eq_decidable_left at beta_at_exists_witness",
                "rewrite eq_decidable_left at beta_at_exists_witness",
                "exact beta_at_exists_witness",
                "right",
                "intro hfull",
                "cases hfull",
                "cases hfull_witness",
                "have hindex : x1 = l \\/ exists h. h + S x1 = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt x1",
                "apply finite_lt_succ_eq_or_lt",
                "exact hfull_witness_left",
                "cases hindex",
                "have hentry : ((exists h. h + S y = S ((S l) * c)) /\\ "
                "exists q. b = q * S ((S l) * c) + y)",
                "rewrite hindex_left at hfull_witness_right",
                "rewrite hindex_left at hfull_witness_right",
                "exact hfull_witness_right",
                "have hxy : x = y",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique l",
                "specialize beta_at_unique x",
                "specialize beta_at_unique y",
                "apply beta_at_unique",
                "exact beta_at_exists_witness",
                "exact hentry",
                "apply eq_decidable_right",
                "exact hxy",
                "apply hpresent_right",
                "exists x1",
                "split",
                "exact hindex_right",
                "exact hfull_witness_right",
            ),
            "Occurrence of a value in a nonempty decoded prefix is constructively decidable.",
        ),
        spec(
            "finite_bounded_prefix_without_top",
            f"forall b c n sn. sn = S n -> ({bounded_succ}) -> "
            f"(forall i. (exists h. h + S i = n) -> ~({top_entry_i})) -> "
            f"({bounded_prefix_n})",
            ("le_succ", "finite_lt_succ_eq_or_lt"),
            (
                "intro b",
                "intro c",
                "intro n",
                "intro sn",
                "intro hsn",
                "intro hbounded",
                "intro hnotop",
                "rewrite hsn at hbounded",
                "rewrite hsn at hbounded",
                "intro i",
                "intro hi",
                "specialize hbounded i",
                "have hfull : exists x. "
                "(((exists h. h + S x = S ((S i) * c)) /\\ "
                "exists q. b = q * S ((S i) * c) + x) /\\ "
                "exists h. h + S x = S n)",
                "apply hbounded",
                "specialize le_succ (S i)",
                "specialize le_succ n",
                "apply le_succ",
                "exact hi",
                "cases hfull",
                "cases hfull_witness",
                "have hsplit : x = n \\/ exists h. h + S x = n",
                "specialize finite_lt_succ_eq_or_lt n",
                "specialize finite_lt_succ_eq_or_lt x",
                "apply finite_lt_succ_eq_or_lt",
                "exact hfull_witness_right",
                "cases hsplit",
                "exfalso",
                "specialize hnotop i",
                "apply hnotop",
                "exact hi",
                "rewrite <- hsplit_left",
                "rewrite <- hsplit_left",
                "exact hfull_witness_left",
                "exists x",
                "split",
                "exact hfull_witness_left",
                "exact hsplit_right",
            ),
            "If a successor prefix omits its top value, its old prefix is bounded by the predecessor.",
        ),
        spec(
            "finite_bounded_last_succ",
            f"forall b c n sn. sn = S n -> ({bounded_succ}) -> exists x. "
            f"(({last_entry_x}) /\\ exists h. h + S x = S n)",
            ("le_refl",),
            (
                "intro b",
                "intro c",
                "intro n",
                "intro sn",
                "intro hsn",
                "intro hbounded",
                "rewrite hsn at hbounded",
                "rewrite hsn at hbounded",
                "specialize hbounded n",
                "apply hbounded",
                "specialize le_refl (S n)",
                "exact le_refl",
            ),
            "A bounded successor prefix exposes a bounded final decoded value.",
        ),
        spec(
            "finite_surjective_succ_intro",
            f"forall b c n sn. sn = S n -> ({surjective_n}) -> "
            f"({last_entry_n}) -> ({surjective_succ})",
            ("finite_lt_succ_eq_or_lt", "le_refl", "le_succ"),
            (
                "intro b",
                "intro c",
                "intro n",
                "intro sn",
                "intro hsn",
                "intro hsurj",
                "intro hlast",
                "rewrite hsn",
                "rewrite hsn",
                "intro y",
                "intro hy",
                "have hsplit : y = n \\/ exists h. h + S y = n",
                "specialize finite_lt_succ_eq_or_lt n",
                "specialize finite_lt_succ_eq_or_lt y",
                "apply finite_lt_succ_eq_or_lt",
                "exact hy",
                "cases hsplit",
                "exists n",
                "split",
                "specialize le_refl (S n)",
                "exact le_refl",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact hlast",
                "specialize hsurj y",
                "have hpre : exists i. "
                "((exists h. h + S i = n) /\\ "
                "((exists h. h + S y = S ((S i) * c)) /\\ "
                "exists q. b = q * S ((S i) * c) + y))",
                "apply hsurj",
                "exact hsplit_right",
                "cases hpre",
                "cases hpre_witness",
                "exists x",
                "split",
                "specialize le_succ (S x)",
                "specialize le_succ n",
                "apply le_succ",
                "exact hpre_witness_left",
                "exact hpre_witness_right",
            ),
            "A surjective prefix plus its new top value is surjective at successor length.",
        ),
        spec(
            "finite_last_is_top_from_prefix_surjective",
            f"forall b c n sn. sn = S n -> ({bounded_succ}) -> "
            f"({injective_succ}) -> ({surjective_n}) -> ({last_entry_n})",
            (
                "finite_bounded_last_succ",
                "finite_lt_succ_eq_or_lt",
                "le_refl",
                "le_succ",
                "lt_irrefl_expanded",
            ),
            (
                "intro b",
                "intro c",
                "intro n",
                "intro sn",
                "intro hsn",
                "intro hbounded",
                "intro hinj",
                "intro hsurj",
                "rewrite hsn at hinj",
                "rewrite hsn at hinj",
                "have hlast : exists x. "
                "(((exists h. h + S x = S ((S n) * c)) /\\ "
                "exists q. b = q * S ((S n) * c) + x) /\\ "
                "exists h. h + S x = S n)",
                "specialize finite_bounded_last_succ b",
                "specialize finite_bounded_last_succ c",
                "specialize finite_bounded_last_succ n",
                "specialize finite_bounded_last_succ sn",
                "apply finite_bounded_last_succ",
                "exact hsn",
                "exact hbounded",
                "cases hlast",
                "cases hlast_witness",
                "have hsplit : x = n \\/ exists h. h + S x = n",
                "specialize finite_lt_succ_eq_or_lt n",
                "specialize finite_lt_succ_eq_or_lt x",
                "apply finite_lt_succ_eq_or_lt",
                "exact hlast_witness_right",
                "cases hsplit",
                "rewrite hsplit_left at hlast_witness_left",
                "rewrite hsplit_left at hlast_witness_left",
                "exact hlast_witness_left",
                "specialize hsurj x",
                "have hpre : exists i. "
                "((exists h. h + S i = n) /\\ "
                "((exists h. h + S x = S ((S i) * c)) /\\ "
                "exists q. b = q * S ((S i) * c) + x))",
                "apply hsurj",
                "exact hsplit_right",
                "cases hpre",
                "cases hpre_witness",
                "have hni : n = x1",
                "specialize hinj n",
                "specialize hinj x1",
                "specialize hinj x",
                "apply hinj",
                "specialize le_refl (S n)",
                "exact le_refl",
                "specialize le_succ (S x1)",
                "specialize le_succ n",
                "apply le_succ",
                "exact hpre_witness_left",
                "exact hlast_witness_left",
                "exact hpre_witness_right",
                "exfalso",
                "specialize lt_irrefl_expanded n",
                "apply lt_irrefl_expanded",
                "rewrite hni",
                "exact hpre_witness_left",
            ),
            "A bounded injective successor sequence must place the new value last once its prefix is surjective.",
        ),
        spec(
            "finite_surjective_succ_from_prefix",
            f"forall b c n sn. sn = S n -> ({bounded_succ}) -> "
            f"({injective_succ}) -> ({surjective_n}) -> ({surjective_succ})",
            (
                "finite_last_is_top_from_prefix_surjective",
                "finite_surjective_succ_intro",
            ),
            (
                "intro b",
                "intro c",
                "intro n",
                "intro sn",
                "intro hsn",
                "intro hbounded",
                "intro hinj",
                "intro hsurj",
                f"have hlast : {last_entry_n}",
                "specialize finite_last_is_top_from_prefix_surjective b",
                "specialize finite_last_is_top_from_prefix_surjective c",
                "specialize finite_last_is_top_from_prefix_surjective n",
                "specialize finite_last_is_top_from_prefix_surjective sn",
                "apply finite_last_is_top_from_prefix_surjective",
                "exact hsn",
                "exact hbounded",
                "exact hinj",
                "exact hsurj",
                "specialize finite_surjective_succ_intro b",
                "specialize finite_surjective_succ_intro c",
                "specialize finite_surjective_succ_intro n",
                "specialize finite_surjective_succ_intro sn",
                "apply finite_surjective_succ_intro",
                "exact hsn",
                "exact hsurj",
                "exact hlast",
            ),
            "The available successor branch extends prefix surjectivity to the full prefix.",
        ),
        spec(
            "finite_no_top_successor_gate",
            f"forall b c n sn. sn = S n -> ({bounded_succ}) -> "
            f"({injective_succ}) -> ~({contains_top}) -> "
            f"(({bounded_prefix_n}) -> ({injective_prefix_n}) -> "
            f"({surjective_n})) -> ({surjective_succ})",
            (
                "finite_bounded_prefix_without_top",
                "finite_injective_prefix_succ",
                "finite_surjective_succ_from_prefix",
            ),
            (
                "intro b",
                "intro c",
                "intro n",
                "intro sn",
                "intro hsn",
                "intro hbounded",
                "intro hinj",
                "intro hmissing",
                "intro hinduction",
                "have hnotop : forall i. (exists h. h + S i = n) -> "
                "~((exists h. h + S n = S ((S i) * c)) /\\ "
                "exists q. b = q * S ((S i) * c) + n)",
                "intro i",
                "intro hi",
                "intro hentry",
                "apply hmissing",
                "exists i",
                "split",
                "exact hi",
                "exact hentry",
                f"have hprefix_bounded : {bounded_prefix_n}",
                "specialize finite_bounded_prefix_without_top b",
                "specialize finite_bounded_prefix_without_top c",
                "specialize finite_bounded_prefix_without_top n",
                "specialize finite_bounded_prefix_without_top sn",
                "apply finite_bounded_prefix_without_top",
                "exact hsn",
                "exact hbounded",
                "exact hnotop",
                f"have hprefix_injective : {injective_prefix_n}",
                "specialize finite_injective_prefix_succ b",
                "specialize finite_injective_prefix_succ c",
                "specialize finite_injective_prefix_succ n",
                "specialize finite_injective_prefix_succ sn",
                "apply finite_injective_prefix_succ",
                "exact hsn",
                "exact hinj",
                f"have hprefix_surjective : {surjective_n}",
                "apply hinduction",
                "exact hprefix_bounded",
                "exact hprefix_injective",
                "specialize finite_surjective_succ_from_prefix b",
                "specialize finite_surjective_succ_from_prefix c",
                "specialize finite_surjective_succ_from_prefix n",
                "specialize finite_surjective_succ_from_prefix sn",
                "apply finite_surjective_succ_from_prefix",
                "exact hsn",
                "exact hbounded",
                "exact hinj",
                "exact hprefix_surjective",
            ),
            "The no-top branch of the constructive successor induction is complete.",
        ),
        spec(
            "finite_bounded_injective_surjective",
            f"forall n b c. ({pigeonhole_bounded}) -> "
            f"({pigeonhole_injective}) -> ({pigeonhole_surjective})",
            (
                "finite_surjective_zero",
                "finite_contains_decidable",
                "finite_bounded_last_succ",
                "beta_prefix_swap_last_from_entries",
                "finite_swap_last_bounded",
                "finite_swap_last_injective",
                "finite_bounded_prefix_without_top",
                "finite_injective_prefix_succ",
                "finite_surjective_succ_from_prefix",
                "finite_swap_last_surjective_back",
                "finite_no_top_successor_gate",
                "beta_at_unique",
                "le_succ",
                "le_refl",
                "lt_irrefl_expanded",
            ),
            (
                "induction n",
                "intro b",
                "intro c",
                "intro hbounded",
                "intro hinjective",
                "specialize finite_surjective_zero b",
                "specialize finite_surjective_zero c",
                "specialize finite_surjective_zero 0",
                "apply finite_surjective_zero",
                "refl",
                "intro b",
                "intro c",
                "intro hbounded",
                "intro hinjective",
                "have hcontains : "
                f"({contains_top}) \\/ ~({contains_top})",
                "specialize finite_contains_decidable b",
                "specialize finite_contains_decidable c",
                "specialize finite_contains_decidable n",
                "specialize finite_contains_decidable n",
                "exact finite_contains_decidable",
                "cases hcontains",
                "cases hcontains_left",
                "cases hcontains_left_witness",
                "have hlast : exists y. "
                "(((exists h. h + S y = S ((S n) * c)) /\\ "
                "exists q. b = q * S ((S n) * c) + y) /\\ "
                "exists h. h + S y = S n)",
                "specialize finite_bounded_last_succ b",
                "specialize finite_bounded_last_succ c",
                "specialize finite_bounded_last_succ n",
                "specialize finite_bounded_last_succ (S n)",
                "apply finite_bounded_last_succ",
                "refl",
                "exact hbounded",
                "cases hlast",
                "cases hlast_witness",
                f"have hswap : {pigeon_swap_contract}",
                "specialize beta_prefix_swap_last_from_entries b",
                "specialize beta_prefix_swap_last_from_entries c",
                "specialize beta_prefix_swap_last_from_entries n",
                "specialize beta_prefix_swap_last_from_entries x",
                "specialize beta_prefix_swap_last_from_entries n",
                "specialize beta_prefix_swap_last_from_entries x1",
                "apply beta_prefix_swap_last_from_entries",
                "exact hcontains_left_witness_left",
                "exact hcontains_left_witness_right",
                "exact hlast_witness_left",
                "cases hswap",
                "cases hswap_witness",
                "cases hswap_witness_witness",
                "cases hswap_witness_witness_right",
                f"have hswap_bounded : {swapped_bounded_succ}",
                "specialize finite_swap_last_bounded b",
                "specialize finite_swap_last_bounded c",
                "specialize finite_swap_last_bounded x2",
                "specialize finite_swap_last_bounded x3",
                "specialize finite_swap_last_bounded n",
                "specialize finite_swap_last_bounded (S n)",
                "specialize finite_swap_last_bounded x",
                "specialize finite_swap_last_bounded n",
                "specialize finite_swap_last_bounded x1",
                "apply finite_swap_last_bounded",
                "refl",
                "exact hcontains_left_witness_left",
                "exact hbounded",
                "exact hcontains_left_witness_right",
                "exact hlast_witness_left",
                "exact hswap_witness_witness_left",
                "exact hswap_witness_witness_right_left",
                "exact hswap_witness_witness_right_right",
                f"have hswap_injective : {swapped_injective_succ}",
                "specialize finite_swap_last_injective b",
                "specialize finite_swap_last_injective c",
                "specialize finite_swap_last_injective x2",
                "specialize finite_swap_last_injective x3",
                "specialize finite_swap_last_injective n",
                "specialize finite_swap_last_injective (S n)",
                "specialize finite_swap_last_injective x",
                "specialize finite_swap_last_injective n",
                "specialize finite_swap_last_injective x1",
                "apply finite_swap_last_injective",
                "refl",
                "exact hcontains_left_witness_left",
                "exact hinjective",
                "exact hcontains_left_witness_right",
                "exact hlast_witness_left",
                "exact hswap_witness_witness_left",
                "exact hswap_witness_witness_right_left",
                "exact hswap_witness_witness_right_right",
                "have hnotop : forall j. (exists h. h + S j = n) -> "
                f"~({swapped_top_at_j})",
                "intro j",
                "intro hj",
                "intro htop",
                "have hjsn : exists h. h + S j = S n",
                "specialize le_succ (S j)",
                "specialize le_succ n",
                "apply le_succ",
                "exact hj",
                "have hnsn : exists h. h + S n = S n",
                "specialize le_refl (S n)",
                "exact le_refl",
                "have hjneq : j = n",
                "specialize hswap_injective j",
                "specialize hswap_injective n",
                "specialize hswap_injective n",
                "apply hswap_injective",
                "exact hjsn",
                "exact hnsn",
                "exact htop",
                "exact hswap_witness_witness_right_left",
                "specialize lt_irrefl_expanded n",
                "apply lt_irrefl_expanded",
                "rewrite hjneq at hj",
                "exact hj",
                f"have hprefix_bounded : {swapped_bounded_prefix}",
                "specialize finite_bounded_prefix_without_top x2",
                "specialize finite_bounded_prefix_without_top x3",
                "specialize finite_bounded_prefix_without_top n",
                "specialize finite_bounded_prefix_without_top (S n)",
                "apply finite_bounded_prefix_without_top",
                "refl",
                "exact hswap_bounded",
                "exact hnotop",
                f"have hprefix_injective : {swapped_injective_prefix}",
                "specialize finite_injective_prefix_succ x2",
                "specialize finite_injective_prefix_succ x3",
                "specialize finite_injective_prefix_succ n",
                "specialize finite_injective_prefix_succ (S n)",
                "apply finite_injective_prefix_succ",
                "refl",
                "exact hswap_injective",
                f"have hprefix_surjective : {swapped_surjective_prefix}",
                "specialize IH x2",
                "specialize IH x3",
                "apply IH",
                "exact hprefix_bounded",
                "exact hprefix_injective",
                f"have hswap_surjective : {swapped_surjective_succ}",
                "specialize finite_surjective_succ_from_prefix x2",
                "specialize finite_surjective_succ_from_prefix x3",
                "specialize finite_surjective_succ_from_prefix n",
                "specialize finite_surjective_succ_from_prefix (S n)",
                "apply finite_surjective_succ_from_prefix",
                "refl",
                "exact hswap_bounded",
                "exact hswap_injective",
                "exact hprefix_surjective",
                "specialize finite_swap_last_surjective_back b",
                "specialize finite_swap_last_surjective_back c",
                "specialize finite_swap_last_surjective_back x2",
                "specialize finite_swap_last_surjective_back x3",
                "specialize finite_swap_last_surjective_back n",
                "specialize finite_swap_last_surjective_back (S n)",
                "specialize finite_swap_last_surjective_back x",
                "specialize finite_swap_last_surjective_back n",
                "specialize finite_swap_last_surjective_back x1",
                "apply finite_swap_last_surjective_back",
                "refl",
                "exact hcontains_left_witness_left",
                "exact hcontains_left_witness_right",
                "exact hlast_witness_left",
                "exact hswap_witness_witness_left",
                "exact hswap_witness_witness_right_left",
                "exact hswap_witness_witness_right_right",
                "exact hswap_surjective",
                "specialize finite_no_top_successor_gate b",
                "specialize finite_no_top_successor_gate c",
                "specialize finite_no_top_successor_gate n",
                "specialize finite_no_top_successor_gate (S n)",
                "apply finite_no_top_successor_gate",
                "refl",
                "exact hbounded",
                "exact hinjective",
                "exact hcontains_right",
                "intro hprefix_bounded",
                "intro hprefix_injective",
                "specialize IH b",
                "specialize IH c",
                "apply IH",
                "exact hprefix_bounded",
                "exact hprefix_injective",
            ),
            "Every bounded injective beta-coded prefix is surjective onto its finite interval.",
        ),
    )


__all__ = [
    "bounded_prefix",
    "bounded_successor_prefix",
    "contains_prefix",
    "injective_prefix",
    "injective_successor_prefix",
    "make_finite_permutation_theorems",
    "permutation_prefix",
    "surjective_prefix",
    "surjective_successor_prefix",
]
