---
title: Peano Lab theorem ladder
tags: [peano-arithmetic, induction, regression, library]
---

The **theorem ladder** is both curriculum and regression suite for [[peano-lab]]. It begins with
$0+n=n$, develops commutativity and associativity of addition and multiplication, proves the
successor lemmas, defines $n\le m$ by an additive witness, establishes the partial-order laws and
totality, and reaches the 23-entry core capstone

$$
\forall n\,m.\;n\cdot m=0\to n=0\lor m=0.
$$

Each named entry stores a closed statement, earlier dependencies, and an exact tactic script. CI
replays the script, packages earlier checked certificates in nested
[[self-contained-proof-sharing|self-contained Cuts]], and submits the closed result to the
[[trusted-kernel]]. Helper lemmas are first-class checked entries, not hidden rewrite axioms or
trusted names.

The browser commands `pa lib <name>` and `pa lean <name>` expose the script and an exact Lean 4
statement stub respectively. Inside a live proof, `use <name>` performs [[checked-theorem-reuse]]
by embedding the rechecked closed certificate in a self-contained Cut.

A [[replayable-proof-script]] may preserve how a live theorem was discovered, but it does not add a
library entry. Admission still requires a reviewed closed statement, earlier dependencies, replay,
kernel check, tests, and a source commit.

M11 extends the twenty-rung core with `one_mul`, `mul_one`, and `add_mul`, completing the original
23-entry oriented
[[commutative-semiring-basis]] needed by proof-producing polynomial normalization.

The M20 branch snapshot adds 28 general nodes to its 23-entry base for a total of 51: equality
congruence, additive cancellation and
zero-sum, order endpoints, nonzero-product and small-factor reasoning, [[divisibility]],
constructive non-divisibility, generic residue algebra, and [[prime_two]] as the first checked
fully expanded prime instance. The checked DAG and its planned route through the general
[[prime-number]] spine and [[fundamental-theorem-of-arithmetic]] live in the
[[arithmetic-library-moc]].

The upstream public-catalog snapshot adds a 26-entry extension to the same original core, for 49
entries in that snapshot. It develops multiples,
residue transport, the five residue cases, square residues, and the capstone
$\neg(5\mid n)\to\exists q.\;n^4=5q+1$. Its source commit and catalog hash are retained, and every
expanded certificate is checked in the empty context. This extension is also a useful seed for a
[[verifier-guided-policy-evaluation-and-search|model-v2 curriculum]], but the capstone itself is now
a library-retrieval test rather than a sealed theorem-discovery benchmark.

The reconciled runtime now has 189 unique checked entries: the 23-entry core,
154 post-baseline foundational entries, and twelve genuinely new modular
capstones. The newer foundation includes discrete order, multiplication
cancellation and monotonicity, and native [[quotient-and-remainder]] existence
and uniqueness, plus the relational [[gcd-and-coprimality]] API through gcd
uniqueness, Euclidean-step invariance, and constructive bounded/general gcd
existence. The next ten-node tranche adds simultaneous balanced Bézout,
[[gauss_coprime_cancel]], [[prime_divisor_eq_one_or_self]], and
[[euclid_prime_dvd_product]]. The newest twelve-node tranche adds constructive
[[eq_decidable|equality]] and [[multiple_decidable|divisibility]] decisions,
bounded [[factor_search_up_to|factor search]], [[prime_or_composite]] and
[[prime_decidable|primality decision]], [[proper_factor_lt|proper-factor
descent]], and [[prime_divisor_exists|prime-divisor existence]].
The newest seven-node tranche closes [[mod_eq_trans|congruence transitivity]],
[[mod_eq_add|addition compatibility]], and the single-position
[[godel-beta-sequence|Gödel-β]] API through [[beta_at_exists_unique]].
The next five-node tranche proves right, left, and two-input multiplication
compatibility through [[mod_eq_mul]], then connects directed decompositions and
β values to congruence with [[remainder_decomposition_to_mod_eq]] and
[[beta_at_to_mod_eq]].
The following three-node reverse tranche proves bounded representative
uniqueness, reconstructs directed remainders with
[[mod_eq_to_remainder_decomposition]], and closes the bounded reverse β bridge
as [[beta_at_of_mod_eq_bound]].
The newest six-node tranche adds [[bezout_mod_left]] and
[[bezout_mod_right]], the subtraction-free
[[mod_eq_predecessor_cancel]], constructive [[binary_crt]], its bounded-residue
form [[binary_crt_remainders]], and the two-position β constructor
[[binary_crt_beta_pair]]. That final theorem retains β-modulus coprimality as
an explicit premise.

The newest six-node tranche proves [[beta_modulus_coprime_base]] and
[[common_divisor_beta_moduli_divides_gap_times_c]], derives
[[beta_moduli_coprime_of_gap_dvd]], and uses it in
[[binary_crt_beta_pair_of_gap_dvd]]. It also constructs bounded nonzero common
multiples through [[bounded_common_multiple_step]] and
[[bounded_common_multiple_exists]]. The coprimality result is intentionally
conditional on `j = i + gap` and `gap | c`; unconditional
pairwise coprimality is false.

The newest seven-node tranche proves ordered and pairwise bounded-prefix
coprimality through
[[beta_moduli_coprime_of_lt_bounded_common_multiple]],
[[beta_moduli_pairwise_coprime_bounded]], and
[[bounded_beta_moduli_pairwise_coprime_exists]]. It then adds product
coprimality via [[coprime_mul_left]] and [[coprime_mul_right]], modulus descent
via [[mod_eq_of_mod_eq_multiple]], and one invariant-preserving CRT extension
via [[binary_crt_fold_step]].

The latest six-node tranche adds [[right_factor_divides_product]], advances the
product and decoded-congruence components through
[[beta_accumulated_product_step]] and
[[beta_crt_prefix_congruence_step]], combines them in
[[beta_crt_prefix_invariant_step]], and closes the ordinary-induction fold as
[[bounded_beta_crt_prefix_invariant]].
[[bounded_beta_crt_for_existing_code]] projects the result only for values
already represented by a supplied `BetaAt` code; it is not arbitrary
finite-sequence coding.

The shared snapshot now totals 242,629 proof nodes and 6,895 self-contained
Cuts across 189 certificates; 149 certificates contain a Cut.
[[bounded_beta_crt_for_existing_code]] is largest at 25,545 nodes and 755 Cuts,
while prime-divisor existence sets the maximum depth at 80. The next
mathematical/representation gate is genuine prefix-product recurrence and
bounds, followed by [[godel-beta-sequence|β finite-prefix recoding]] and
greatest-prime descent;
[[fundamental-theorem-of-arithmetic|FTA]] is not yet a native checked theorem.

## Related

[[peano-lab]] · [[proof-certificate]] · [[replayable-proof-script]] · [[substitution]] ·
[[self-contained-proof-sharing]] · [[intuitionistic-logic]] ·
[[foundational-arithmetic-library]]
