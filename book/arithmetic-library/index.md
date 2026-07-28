# The foundational arithmetic library

This part turns Peano Lab's original theorem ladder into a general-purpose,
dependency-organized arithmetic library. The fourth-power-modulo-five exercise
was a useful stress test, but it is now only one possible application. The
organizing spine is reusable mathematics:

$$
\text{equality}
\to \text{semiring laws}
\to \text{order}
\to \text{divisibility}
\to \text{congruence}
\to \text{division}
\to \gcd
\to \text{primes}
\to \text{factorization}.
$$

The current candidate snapshot contains **164 replayed, closed, independently
kernel-checked Peano theorems**. One hundred and twenty-nine form the post-baseline
foundational layer: named equality congruences, additive cancellation, discrete order,
multiplication cancellation and monotonicity, zero-sum and nonzero-product
facts, divisibility closure, constructive non-divisibility, generic residue
algebra, constructive quotient-remainder existence and uniqueness, and the
relational gcd/coprimality API through gcd uniqueness and both directions of
Euclidean gcd invariance, plus constructive bounded and general gcd existence,
balanced-natural Bézout, Gauss cancellation, and Euclid's lemma. It now also
contains constructive equality and divisibility decisions, bounded factor-pair
search, the prime-or-composite decision, proper-factor descent, and prime-divisor
existence. The latest congruence and encoding tranches prove balanced
modular-congruence transitivity and compatibility with addition and
multiplication, turn quotient-remainder decompositions into congruences, then
check single-position Gödel-β decoding moduli, self-decoding below the bound,
decoded-value existence, uniqueness, their combined
existence-and-uniqueness interface, and both directions between a decoded
value and a bounded balanced-congruence witness. Bounded congruent
representatives are now unique, and a bounded congruence can be reconstructed
as a directed quotient-remainder decomposition. This layer
includes `prime_two`, the first checked instance of the fully expanded prime
predicate, `prime_divisor_eq_one_or_self`, its general divisor
characterization, and `euclid_prime_dvd_product`.
The reconciled upstream modular catalog contributes twelve
more unique residue and fourth-power theorems; fourteen of its other records
are identical to foundational entries and are exposed only once.

Every current theorem fits the browser's ordinary `use` limit. The largest
shared certificate, `euclid_prime_dvd_product`, has 5,382 structural proof
nodes and depth 55; `prime_divisor_exists` sets the snapshot-wide maximum
depth at 80. Across all 164 entries, the snapshot contains 79,763 structural
nodes, including 2,138 self-contained Cuts, and 124 certificates contain at
least one Cut. The largest per-certificate Cut count is 159, again at
`euclid_prime_dvd_product`. The
immutable upstream
report still records the capstone's former fully expanded 21,515-node/depth-66
representation; it remains provenance, not the current runtime metric.

That number is deliberately narrower than the 171-node research catalog: 23
nodes are `checked_existing`, 141 are `checked_m20`, three are
`planned_expressible`, and four are `blocked_by_language`. Beyond
`prime_two`, the catalog now includes checked relational gcd existence,
balanced Bézout, Gauss cancellation, Euclid's lemma, constructive primality
decisions, prime-divisor existence, additive and multiplicative
modular-congruence compatibility, the decomposition-to-congruence bridge, and
Gödel-β decoded-value totality, functionality, and its bidirectional bounded
congruence characterization. The remaining
expressible targets are `prime_three`, primes above every bound, and a
two-prime-product uniqueness client. Greatest-prime descent, binary and
bounded CRT, finite-prefix extension, and the selected encoded-product
infrastructure are the next critical native
factorization gates. A separate
Lean 4 companion now checks full finite-list FTA
existence and uniqueness up to permutation. It is cataloged as a companion,
not counted among the 164 Peano theorems; those entries are not presented as
Peano-proved until a script and closed certificate pass the same kernel gate.

## How to read the status labels

| Label | Meaning |
|---|---|
| `checked_existing` | Already in the original 23-theorem Peano ladder. |
| `checked_m20` | Checked post-baseline extension, including compatible upstream modular entries. |
| `planned_expressible` | Stateable in today's first-order Peano language, but not yet admitted. |
| `blocked_by_language` | Needs a representation/interface not yet implemented as an expanded, checked Peano target. |

For the β-coded factorization entries, `blocked_by_language` describes the
missing expanded authoring interface, not a limitation of first-order PA. The
selected β relations are expressible with natural-number codes; their hygienic
expanders and proof infrastructure have not yet been admitted.

There is no status called “obvious.” A familiar mathematical fact and a
checked theorem are different repository objects.

## Reading route

1. {doc}`Language, notation, and trust <language-and-trust>` explains why
   divisibility and primality are expanded formulas rather than new kernel
   predicates.
2. {doc}`Self-contained proof sharing <proof-sharing>` explains the reviewed
   Cut certificate rule, its trust cost, and why erasure remains an untrusted
   compatibility audit.
3. {doc}`The dependency ladder <dependency-ladder>` gives the complete
   architecture from equality through factorization.
4. {doc}`Divisibility and congruence <divisibility-and-congruence>` develops
   the checked first layer and the balanced natural-number encoding of modular
   congruence.
5. {doc}`GCD and balanced Bézout construction <gcd-and-bezout>` follows the
   checked bounded descent through Gauss cancellation.
6. {doc}`Primes and unique factorization <primes-and-factorization>` separates
   what can be formalized now from the finite-sequence milestone needed for a
   clean Fundamental Theorem of Arithmetic.
7. {doc}`Sources and clean-room provenance <source-audit>` maps the Natural
   Number Game, *The Mechanics of Proof*, and *An Illustrated Theory of
   Numbers* into the corpus without silently copying material.
8. {doc}`Using and extending the library <using-the-library>` shows the live
   workflow and the admission contract.

## Four synchronized views

One stable theorem name is intended to identify the same object in four views:

- the executable `TheoremSpec` and its kernel-checked certificate;
- the generated JSON snapshot and Mermaid dependency graph;
- the explanatory Jupyter Book anchor;
- the atomic Obsidian concept or lemma note.

The generated artifact binds the exact statement, dependency list, tactic
script, certificate representation hash, node count, depth, and one ordered
root digest. These hashes make drift visible; they do not grant authority.
Authority still comes only from checking the closed proof term against the
closed formula.
