"""Constructive first rows of the relational-LCM totality ladder.

Rows A and B connect balanced Bezout result one to coprimality and prove that
the product of coprime inputs is their relational LCM.  Row C proves that
nonzero left scaling preserves the universal LCM relation.  Row D cancels a
nonzero common gcd factor from a balanced Bezout equation, and Row E shows
that a zero relational gcd forces both inputs to be zero.  Row F combines the
ladder into compatible gcd and lcm witnesses satisfying ``g*l = a*b``, with
the zero-input branch retained explicitly.  Rows G--I project relational LCM
totality, package its unique value, and transfer the compatible product law to
arbitrary relational gcd and LCM witnesses.  Compound terms pass through a
parser-validated expander before interpolation; no raw term string is trusted.
Every candidate is dependency-curried, unregistered, and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.kernel.terms import parse_term_in_context, pretty_term
from peano_lab.library.ha_canonical_gcd_candidate import is_gcd
from peano_lab.library.ha_relational_lcm_candidate import (
    _expand_is_lcm,
    is_lcm,
)


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


def _product_is_lcm(left: str, right: str, *, tag: str) -> str:
    """Expand IsLCM(left * right,left,right) through a narrow safe surface."""

    left = _identifier(left, "left product operand")
    right = _identifier(right, "right product operand")
    return _expand_is_lcm(
        f"{left} * {right}", left, right, tag=tag
    )


def _term_is_lcm(
    lcm: str,
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    """Safely expand ``IsLCM`` for parser-validated compound terms.

    ``_expand_is_lcm`` is intentionally a raw alpha-expansion helper and must
    not receive compound user text.  This companion parses every term against
    an explicit finite variable context, renders it canonically, parenthesizes
    non-atoms, and independently checks binder capture before constructing the
    formula used by Row C.
    """

    if (
        not isinstance(variables, tuple)
        or not variables
        or len(set(variables)) != len(variables)
    ):
        raise ValueError("term context must be a nonempty tuple of distinct identifiers")
    checked_variables = tuple(
        _identifier(variable, "term context variable")
        for variable in variables
    )
    context = list(checked_variables)

    def checked_term(source: str) -> str:
        if not isinstance(source, str):
            raise ValueError("LCM term must be parser text")
        term = parse_term_in_context(source, context)
        rendered = pretty_term(term, context).replace("·", "*")
        if rendered in checked_variables or rendered in {"0", "1"}:
            return rendered
        return f"({rendered})"

    lcm_term = checked_term(lcm)
    left_term = checked_term(left)
    right_term = checked_term(right)
    safe_tag = _identifier(tag, "binder tag")
    names = {
        role: f"hscale_{role}_{safe_tag}"
        for role in (
            "left_factor",
            "right_factor",
            "common",
            "left_common",
            "right_common",
            "least_factor",
        )
    }
    if len(set(names.values())) != len(names) or (
        set(names.values()) & set(checked_variables)
    ):
        raise ValueError("generated scaled-IsLCM binder captures an argument")

    return (
        f"(((exists {names['left_factor']}. "
        f"{lcm_term} = {left_term} * {names['left_factor']}) /\\ "
        f"(exists {names['right_factor']}. "
        f"{lcm_term} = {right_term} * {names['right_factor']})) /\\ "
        f"forall {names['common']}. "
        f"(exists {names['left_common']}. "
        f"{names['common']} = {left_term} * {names['left_common']}) -> "
        f"(exists {names['right_common']}. "
        f"{names['common']} = {right_term} * {names['right_common']}) -> "
        f"exists {names['least_factor']}. "
        f"{names['common']} = {lcm_term} * {names['least_factor']})"
    )


def make_ha_lcm_totality_bridge_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build Rows A--I of the constructive gcd--LCM route."""

    coprime_product_lcm = _product_is_lcm(
        "a", "b", tag="coprime_product"
    )
    scale_variables = ("k", "l", "a", "b")
    scale_source_lcm = _term_is_lcm(
        "l",
        "a",
        "b",
        tag="source",
        variables=scale_variables,
    )
    scale_target_lcm = _term_is_lcm(
        "k * l",
        "k * a",
        "k * b",
        tag="target",
        variables=scale_variables,
    )
    gcd_zero_relation = is_gcd("g", "a", "b", tag="zero_inputs")
    compatible_gcd = is_gcd("g", "a", "b", tag="compatible")
    compatible_lcm = is_lcm("l", "a", "b", tag="compatible")
    compatible_zero_lcm = is_lcm(
        "0", "0", "0", tag="compatible_zero"
    )
    compatible_base_lcm = _product_is_lcm(
        "x1", "x2", tag="compatible_base"
    )
    compatible_scaled_lcm = _term_is_lcm(
        "x * (x1 * x2)",
        "x * x1",
        "x * x2",
        tag="compatible_scaled",
        variables=("x", "x1", "x2"),
    )
    existence_lcm = is_lcm("l", "a", "b", tag="existence")
    unique_chosen_lcm = is_lcm(
        "l", "a", "b", tag="unique_chosen"
    )
    unique_compared_lcm = is_lcm(
        "m", "a", "b", tag="unique_compared"
    )
    product_gcd = is_gcd("g", "a", "b", tag="product_gcd_assumption")
    product_lcm = is_lcm(
        "l", "a", "b", tag="product_lcm_assumption"
    )
    gcd_balanced_bezout_payload = (
        "exists d. ((((exists x. a = d * x) /\\ "
        "(exists y. b = d * y)) /\\ forall c. "
        "(exists u. a = c * u) -> (exists v. b = c * v) -> "
        "exists w. d = c * w) /\\ exists xp yp xn yn. "
        "a * xp + b * yp = d + (a * xn + b * yn))"
    )

    return (
        spec(
            "balanced_bezout_one_implies_coprime",
            "forall a b xp yp xn yn. "
            "a * xp + b * yp = 1 + (a * xn + b * yn) -> "
            "forall d. (exists u. a = d * u) -> "
            "(exists v. b = d * v) -> d = 1",
            (
                "common_divisor_divides_balanced_result",
                "divisor_one",
            ),
            (
                "intro a",
                "intro b",
                "intro xp",
                "intro yp",
                "intro xn",
                "intro yn",
                "intro hbez",
                "intro d",
                "intro ha",
                "intro hb",
                "specialize divisor_one d",
                "apply divisor_one",
                "specialize common_divisor_divides_balanced_result d",
                "specialize common_divisor_divides_balanced_result a",
                "specialize common_divisor_divides_balanced_result b",
                "specialize common_divisor_divides_balanced_result 1",
                "specialize common_divisor_divides_balanced_result xp",
                "specialize common_divisor_divides_balanced_result yp",
                "specialize common_divisor_divides_balanced_result xn",
                "specialize common_divisor_divides_balanced_result yn",
                "apply common_divisor_divides_balanced_result",
                "exact ha",
                "exact hb",
                "exact hbez",
            ),
            "A balanced natural Bezout equation with result one forces the "
            "two inputs to be coprime.",
        ),
        spec(
            "coprime_product_is_lcm",
            "forall a b. (forall d. (exists u. a = d * u) -> "
            "(exists v. b = d * v) -> d = 1) -> "
            f"({coprime_product_lcm})",
            (
                "mul_comm",
                "gauss_coprime_cancel",
                "mul_assoc",
            ),
            (
                "intro a",
                "intro b",
                "intro hcop",
                "split",
                "split",
                "exists b",
                "refl",
                "exists a",
                "apply mul_comm",
                "intro c",
                "intro ha",
                "intro hb",
                "cases ha",
                "cases hb",
                "have hdiv : exists q. b * x1 = a * q",
                "exists x",
                "trans c",
                "symm",
                "exact hb_witness",
                "exact ha_witness",
                "have hfactor : exists w. x1 = a * w",
                "specialize gauss_coprime_cancel a",
                "specialize gauss_coprime_cancel b",
                "specialize gauss_coprime_cancel x1",
                "apply gauss_coprime_cancel",
                "exact hcop",
                "exact hdiv",
                "cases hfactor",
                "exists x2",
                "trans b * x1",
                "exact hb_witness",
                "trans b * (a * x2)",
                "rewrite hfactor_witness",
                "refl",
                "trans (b * a) * x2",
                "symm",
                "apply mul_assoc",
                "congr",
                "apply mul_comm",
                "refl",
            ),
            "The product of coprime naturals satisfies the universal "
            "relational LCM specification.",
        ),
        spec(
            "is_lcm_scale_nonzero",
            f"forall k l a b. ~(k = 0) -> ({scale_source_lcm}) -> "
            f"({scale_target_lcm})",
            (
                "mul_assoc",
                "mul_left_cancel_nonzero",
            ),
            (
                "intro k",
                "intro l",
                "intro a",
                "intro b",
                "intro hk",
                "intro h",
                "cases h",
                "cases h_left",
                "cases h_left_left",
                "cases h_left_right",
                "split",
                "split",
                "exists x",
                "rewrite h_left_left_witness",
                "symm",
                "apply mul_assoc",
                "exists x1",
                "rewrite h_left_right_witness",
                "symm",
                "apply mul_assoc",
                "intro c",
                "intro hca",
                "intro hcb",
                "cases hca",
                "cases hcb",
                "have hca_norm : c = k * (a * x2)",
                "trans (k * a) * x2",
                "exact hca_witness",
                "apply mul_assoc",
                "have hcb_norm : c = k * (b * x3)",
                "trans (k * b) * x3",
                "exact hcb_witness",
                "apply mul_assoc",
                "have hab : a * x2 = b * x3",
                "specialize mul_left_cancel_nonzero k",
                "specialize mul_left_cancel_nonzero (a * x2)",
                "specialize mul_left_cancel_nonzero (b * x3)",
                "apply mul_left_cancel_nonzero",
                "exact hk",
                "trans c",
                "symm",
                "exact hca_norm",
                "exact hcb_norm",
                "have hleast : exists w. a * x2 = l * w",
                "specialize h_right (a * x2)",
                "apply h_right",
                "exists x2",
                "refl",
                "exists x3",
                "exact hab",
                "cases hleast",
                "exists x4",
                "trans k * (a * x2)",
                "exact hca_norm",
                "trans k * (l * x4)",
                "congr",
                "refl",
                "exact hleast_witness",
                "symm",
                "apply mul_assoc",
            ),
            "A nonzero common left scale preserves the universal relational "
            "LCM specification.",
        ),
        spec(
            "balanced_bezout_cancel_gcd",
            "forall g a b A B xp yp xn yn. ~(g = 0) -> "
            "a = g * A -> b = g * B -> "
            "a * xp + b * yp = g + (a * xn + b * yn) -> "
            "A * xp + B * yp = 1 + (A * xn + B * yn)",
            (
                "mul_left_cancel_nonzero",
                "mul_add",
                "mul_assoc",
                "mul_one",
            ),
            (
                "intro g",
                "intro a",
                "intro b",
                "intro A",
                "intro B",
                "intro xp",
                "intro yp",
                "intro xn",
                "intro yn",
                "intro hg",
                "intro ha",
                "intro hb",
                "intro hbez",
                "specialize mul_left_cancel_nonzero g",
                "specialize mul_left_cancel_nonzero (A * xp + B * yp)",
                "specialize mul_left_cancel_nonzero "
                "(1 + (A * xn + B * yn))",
                "apply mul_left_cancel_nonzero",
                "exact hg",
                "trans g * (A * xp) + g * (B * yp)",
                "apply mul_add",
                "trans (g * A) * xp + (g * B) * yp",
                "congr",
                "symm",
                "apply mul_assoc",
                "symm",
                "apply mul_assoc",
                "trans a * xp + b * yp",
                "rewrite ha",
                "rewrite hb",
                "refl",
                "trans g + (a * xn + b * yn)",
                "exact hbez",
                "trans g + ((g * A) * xn + (g * B) * yn)",
                "rewrite ha",
                "rewrite hb",
                "refl",
                "trans g * 1 + ((g * A) * xn + (g * B) * yn)",
                "congr",
                "symm",
                "apply mul_one",
                "refl",
                "trans g * 1 + (g * (A * xn) + g * (B * yn))",
                "congr",
                "refl",
                "congr",
                "apply mul_assoc",
                "apply mul_assoc",
                "trans g * 1 + g * (A * xn + B * yn)",
                "congr",
                "refl",
                "symm",
                "apply mul_add",
                "symm",
                "apply mul_add",
            ),
            "Cancel a nonzero common gcd factor from a balanced Bezout "
            "equation.",
        ),
        spec(
            "gcd_zero_inputs",
            f"forall g a b. g = 0 -> ({gcd_zero_relation}) -> "
            "(a = 0 /\\ b = 0)",
            ("mul_zero_left",),
            (
                "intro g",
                "intro a",
                "intro b",
                "intro hg",
                "intro h",
                "cases h",
                "cases h_left",
                "cases h_left_left",
                "cases h_left_right",
                "split",
                "trans g * x",
                "exact h_left_left_witness",
                "rewrite hg",
                "apply mul_zero_left",
                "trans g * x1",
                "exact h_left_right_witness",
                "rewrite hg",
                "apply mul_zero_left",
            ),
            "A zero relational gcd can divide only the zero input pair.",
        ),
        spec(
            "gcd_lcm_compatible_exists",
            f"forall a b. exists g l. ((({compatible_gcd}) /\\ "
            f"({compatible_lcm})) /\\ g * l = a * b)",
            (
                "gcd_balanced_bezout_exists",
                "eq_decidable",
                "gcd_zero_inputs",
                "is_lcm_zero_left",
                "balanced_bezout_cancel_gcd",
                "balanced_bezout_one_implies_coprime",
                "coprime_product_is_lcm",
                "is_lcm_scale_nonzero",
                "mul_assoc",
                "mul_comm",
            ),
            (
                "intro a",
                "intro b",
                f"have hgb : {gcd_balanced_bezout_payload}",
                "specialize gcd_balanced_bezout_exists a",
                "specialize gcd_balanced_bezout_exists b",
                "apply gcd_balanced_bezout_exists",
                "cases hgb",
                "cases hgb_witness",
                "have hzero : x = 0 \\/ ~(x = 0)",
                "specialize eq_decidable x",
                "specialize eq_decidable 0",
                "exact eq_decidable",
                "cases hzero",
                "have habzero : a = 0 /\\ b = 0",
                "specialize gcd_zero_inputs x",
                "specialize gcd_zero_inputs a",
                "specialize gcd_zero_inputs b",
                "apply gcd_zero_inputs",
                "exact hzero_left",
                "exact hgb_witness_left",
                "cases habzero",
                f"have hlcmzero : ({compatible_zero_lcm})",
                "specialize is_lcm_zero_left 0",
                "exact is_lcm_zero_left",
                "exists x",
                "exists 0",
                "split",
                "split",
                "exact hgb_witness_left",
                "rewrite habzero_left",
                "rewrite habzero_left",
                "rewrite habzero_right",
                "rewrite habzero_right",
                "exact hlcmzero",
                "rewrite hzero_left",
                "rewrite habzero_left",
                "rewrite habzero_right",
                "refl",
                "cases hgb_witness_left",
                "cases hgb_witness_left_left",
                "cases hgb_witness_left_left_left",
                "cases hgb_witness_left_left_right",
                "cases hgb_witness_right",
                "cases hgb_witness_right_witness",
                "cases hgb_witness_right_witness_witness",
                "cases hgb_witness_right_witness_witness_witness",
                "have hquotbez : x1 * x3 + x2 * x4 = "
                "1 + (x1 * x5 + x2 * x6)",
                "specialize balanced_bezout_cancel_gcd x",
                "specialize balanced_bezout_cancel_gcd a",
                "specialize balanced_bezout_cancel_gcd b",
                "specialize balanced_bezout_cancel_gcd x1",
                "specialize balanced_bezout_cancel_gcd x2",
                "specialize balanced_bezout_cancel_gcd x3",
                "specialize balanced_bezout_cancel_gcd x4",
                "specialize balanced_bezout_cancel_gcd x5",
                "specialize balanced_bezout_cancel_gcd x6",
                "apply balanced_bezout_cancel_gcd",
                "exact hzero_right",
                "exact hgb_witness_left_left_left_witness",
                "exact hgb_witness_left_left_right_witness",
                "exact hgb_witness_right_witness_witness_witness_witness",
                "have hcop : forall d. (exists u. x1 = d * u) -> "
                "(exists v. x2 = d * v) -> d = 1",
                "specialize balanced_bezout_one_implies_coprime x1",
                "specialize balanced_bezout_one_implies_coprime x2",
                "specialize balanced_bezout_one_implies_coprime x3",
                "specialize balanced_bezout_one_implies_coprime x4",
                "specialize balanced_bezout_one_implies_coprime x5",
                "specialize balanced_bezout_one_implies_coprime x6",
                "apply balanced_bezout_one_implies_coprime",
                "exact hquotbez",
                f"have hbase : ({compatible_base_lcm})",
                "specialize coprime_product_is_lcm x1",
                "specialize coprime_product_is_lcm x2",
                "apply coprime_product_is_lcm",
                "exact hcop",
                f"have hscaled : ({compatible_scaled_lcm})",
                "specialize is_lcm_scale_nonzero x",
                "specialize is_lcm_scale_nonzero (x1 * x2)",
                "specialize is_lcm_scale_nonzero x1",
                "specialize is_lcm_scale_nonzero x2",
                "apply is_lcm_scale_nonzero",
                "exact hzero_right",
                "exact hbase",
                "exists x",
                "exists x * (x1 * x2)",
                "split",
                "split",
                "exact hgb_witness_left",
                "rewrite hgb_witness_left_left_left_witness",
                "rewrite hgb_witness_left_left_left_witness",
                "rewrite hgb_witness_left_left_right_witness",
                "rewrite hgb_witness_left_left_right_witness",
                "exact hscaled",
                "rewrite hgb_witness_left_left_left_witness",
                "rewrite hgb_witness_left_left_right_witness",
                "trans x * (x1 * (x * x2))",
                "congr",
                "refl",
                "trans (x * x1) * x2",
                "symm",
                "apply mul_assoc",
                "trans (x1 * x) * x2",
                "congr",
                "apply mul_comm",
                "refl",
                "apply mul_assoc",
                "symm",
                "apply mul_assoc",
            ),
            "Every pair has compatible relational gcd and lcm witnesses "
            "whose product is the product of the inputs, including zero "
            "inputs.",
        ),
        spec(
            "lcm_exists_relational",
            f"forall a b. exists l. ({existence_lcm})",
            ("gcd_lcm_compatible_exists",),
            (
                "intro a",
                "intro b",
                "specialize gcd_lcm_compatible_exists a",
                "specialize gcd_lcm_compatible_exists b",
                "cases gcd_lcm_compatible_exists",
                "cases gcd_lcm_compatible_exists_witness",
                "cases gcd_lcm_compatible_exists_witness_witness",
                "cases gcd_lcm_compatible_exists_witness_witness_left",
                "exists x1",
                "exact gcd_lcm_compatible_exists_witness_witness_left_right",
            ),
            "Every pair of naturals has a relational LCM; this is the "
            "direct LCM projection of the compatible pair theorem.",
        ),
        spec(
            "canonical_lcm_exists_unique",
            f"forall a b. exists l. (({unique_chosen_lcm}) /\\ "
            f"forall m. ({unique_compared_lcm}) -> m = l)",
            (
                "lcm_exists_relational",
                "is_lcm_unique",
            ),
            (
                "intro a",
                "intro b",
                "specialize lcm_exists_relational a",
                "specialize lcm_exists_relational b",
                "cases lcm_exists_relational",
                "exists x",
                "split",
                "exact lcm_exists_relational_witness",
                "intro m",
                "intro hm",
                "specialize is_lcm_unique m",
                "specialize is_lcm_unique x",
                "specialize is_lcm_unique a",
                "specialize is_lcm_unique b",
                "apply is_lcm_unique",
                "exact hm",
                "exact lcm_exists_relational_witness",
            ),
            "The relational LCM value exists uniquely; divisibility "
            "witnesses themselves are not claimed to be unique.",
        ),
        spec(
            "gcd_lcm_product",
            f"forall g l a b. ({product_gcd}) -> ({product_lcm}) -> "
            "g * l = a * b",
            (
                "gcd_lcm_compatible_exists",
                "is_gcd_unique",
                "is_lcm_unique",
            ),
            (
                "intro g",
                "intro l",
                "intro a",
                "intro b",
                "intro hg",
                "intro hl",
                "specialize gcd_lcm_compatible_exists a",
                "specialize gcd_lcm_compatible_exists b",
                "cases gcd_lcm_compatible_exists",
                "cases gcd_lcm_compatible_exists_witness",
                "cases gcd_lcm_compatible_exists_witness_witness",
                "cases gcd_lcm_compatible_exists_witness_witness_left",
                "have hgeq : g = x",
                "specialize is_gcd_unique g",
                "specialize is_gcd_unique x",
                "specialize is_gcd_unique a",
                "specialize is_gcd_unique b",
                "apply is_gcd_unique",
                "exact hg",
                "exact gcd_lcm_compatible_exists_witness_witness_left_left",
                "have hleq : l = x1",
                "specialize is_lcm_unique l",
                "specialize is_lcm_unique x1",
                "specialize is_lcm_unique a",
                "specialize is_lcm_unique b",
                "apply is_lcm_unique",
                "exact hl",
                "exact gcd_lcm_compatible_exists_witness_witness_left_right",
                "rewrite hgeq",
                "rewrite hleq",
                "exact gcd_lcm_compatible_exists_witness_witness_right",
            ),
            "Any relational gcd and LCM pair satisfies the gcd--LCM "
            "product identity, by uniqueness from a compatible pair.",
        ),
    )


__all__ = ["make_ha_lcm_totality_bridge_candidate_theorems"]
