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

The reconciled runtime now has 164 unique checked entries: the 23-entry core,
129 post-baseline foundational entries, and twelve genuinely new modular
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

The shared snapshot now totals 79,763 proof nodes and 2,138 self-contained
Cuts across 164 certificates; 124 certificates contain a Cut. Euclid's lemma
remains largest at 5,382 nodes, while prime-divisor existence sets the maximum
depth at 80. The next mathematical/representation gate is greatest-prime
descent followed by CRT, [[godel-beta-sequence|β finite-prefix]], and
prefix-product infrastructure; [[fundamental-theorem-of-arithmetic|FTA]] is
not yet a native checked theorem.

## Related

[[peano-lab]] · [[proof-certificate]] · [[replayable-proof-script]] · [[substitution]] ·
[[self-contained-proof-sharing]] · [[intuitionistic-logic]] ·
[[foundational-arithmetic-library]]
