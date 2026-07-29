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

The previous published snapshot contains **189 replayed, closed, independently
kernel-checked Peano theorems**. One hundred and fifty-four form the post-baseline
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
as a directed quotient-remainder decomposition. The preceding six-theorem tranche
extracts the two modular consequences of balanced Bézout, proves the
successor-modulus predecessor cancellation used by the constructive witness, checks
binary CRT for arbitrary nonzero coprime natural moduli, exposes bounded
solutions as two directed quotient-remainder equations, and constructs one
code realizing two bounded β values whenever the two expanded β moduli are
given coprime. This layer
includes `prime_two`, the first checked instance of the fully expanded prime
predicate, `prime_divisor_eq_one_or_self`, its general divisor
characterization, and `euclid_prime_dvd_product`.
The latest six entries close the next conditional encoding checkpoint:
`beta_modulus_coprime_base`,
`common_divisor_beta_moduli_divides_gap_times_c`,
`beta_moduli_coprime_of_gap_dvd`,
`binary_crt_beta_pair_of_gap_dvd`,
`bounded_common_multiple_step`, and
`bounded_common_multiple_exists`. They prove pairwise beta-modulus
coprimality when $j=i+\mathit{gap}$ and $\mathit{gap}\mid c$, then construct a
nonzero $c$ divisible by every positive natural up to a given bound.
Seven further entries turn that resource into bounded-prefix pairwise
coprimality, close coprimality under products in both orientations, descend
balanced congruence from a product modulus to any divisor modulus, and prove
the universal preservation invariant of `binary_crt_fold_step`. That fold
step preserves every old congruence whose modulus divides the accumulated
product while adding the requested congruence for one new coprime modulus.
Six more entries now carry this algebra through a genuine ordinary-induction
fold. `right_factor_divides_product` supplies the new factor's explicit
divisibility witness. `beta_accumulated_product_step` preserves a nonzero
accumulated product, divisibility by every earlier beta modulus, and
coprimality with every future bounded beta modulus.
`beta_crt_prefix_congruence_step` extends congruence to the next value decoded
from a supplied code, and `beta_crt_prefix_invariant_step` combines the two
successor arguments. Finally, `bounded_beta_crt_prefix_invariant` constructs
the full four-part invariant at every bounded prefix, and
`bounded_beta_crt_for_existing_code` projects its congruence component at the
full bound.

At that checkpoint, the last wrapper had to be read narrowly. Its residues are already decoded
from the input code $b$, so extensionally one could choose $z=b$. It does not
construct a beta code for an independently specified finite sequence and is
not the missing finite-prefix recoding theorem.
The reconciled upstream modular catalog contributed twelve
more unique residue and fourth-power theorems; fourteen of its other records
are identical to foundational entries and are exposed only once.

Every theorem in that published snapshot fit its browser `use` limit. The largest
shared certificate, `bounded_beta_crt_for_existing_code`, has 25,545 structural
proof nodes, depth 79, and 755 self-contained Cuts; `prime_divisor_exists`
still sets the snapshot-wide maximum depth at 80. Across all 189 entries, the
snapshot contains 242,629 structural nodes, including 6,895 Cuts, and 149 certificates
contain at least one Cut. The
immutable upstream
report still records the capstone's former fully expanded 21,515-node/depth-66
representation; it remains provenance, not the current runtime metric.

Those historical counts were narrower than the then-196-node research catalog: 23
nodes are `checked_existing`, 166 are `checked_m20`, three are
`planned_expressible`, and four are `blocked_by_language`. Beyond
`prime_two`, the catalog now includes checked relational gcd existence,
balanced Bézout, Gauss cancellation, Euclid's lemma, constructive primality
decisions, prime-divisor existence, additive and multiplicative
modular-congruence compatibility, the decomposition-to-congruence bridge, and
Gödel-β decoded-value totality, functionality, its bidirectional bounded
congruence characterization, constructive binary CRT, the conditional
gap-divisibility coprimality theorem, its two-position beta-code client,
bounded common-multiple existence, bounded-prefix pairwise coprimality,
product coprimality, modulus descent, the generic CRT fold step, and its
ordinary-induction prefix invariant for already decoded values.

That boundary has now advanced. At this integration checkpoint the native
sorted Gödel-β route checks finite-prefix recoding and extension, exact
prefix-product traces and Product functionality, greatest-prime-divisor
descent, canonical append, factorization existence, and canonical extensional
uniqueness.

| Endpoint | Nodes | Depth | Cuts |
|---|---:|---:|---:|
| `prime_factorization_existence` | 43,973 | 98 | 1,328 |
| `prime_factorization_uniqueness` | 29,789 | 82 | 854 |
| `fundamental_theorem_of_arithmetic` | 73,767 | 99 | 2,184 |

The exact FTA certificate SHA-256 is
`fd978f59bf3b0aa7b6c9ec1bc92ab5e7bbf949c25309173e098bd8f3b8de0958`.
It checks from the empty context and passes the full prove/use/exact/QED path
under the current 100,000-node/depth-256 cap. It uses only PA1–PA6 and
induction and contains no DNE. Runtime integration is complete. The current
runtime has 247 checked theorems: 23 baseline, 212 general foundational, and
twelve fixed modular capstones. The synchronized 248-entry research catalog
has 23 `checked_existing`, 224 `checked_m20`, no planned record, and one
representation-blocked record. The generated snapshot has 982,534 nodes,
28,892 Cuts, 204 Cut-bearing certificates, ordered root
`eb4775dfd181dc5e45bec463a93f14b0ea9d02501c40c5167b7cae77cd4ff432`,
and source digest
`295ca3b65970324e7d2ed51b57dc4510227b0abbc2d35b68a809dbde26aba868`.
The vault has 327 notes and 3,287 links; corpus and browser identities are
recorded in {doc}`Using and extending the library <using-the-library>`.

The added `prime_unbounded` theorem is constructive and independent of FTA.
It takes a nonzero common multiple of every positive value through `n`, chooses
a prime divisor of its successor, and proves that divisor is above `n`: a
prime at or below the bound would divide both consecutive numbers and hence
one. Its certificate has 4,595 nodes, depth 82, 146 Cuts, and SHA-256
`8a44fb2d207c2a41684de6d6630674f3f3b951cd036f733b3dd493321099d37b`.
It uses PA1–PA6 only, has no DNE, and passes dependency, PA, hypothesis, and
live-use audits.

This native result is not the conventional list theorem. Peano Lab still has
no primitive list or multiset type; factors and prefix products are β-coded,
and uniqueness compares lengths and decoded bounded entries rather than raw
codes. A separate Lean 4 companion checks list existence and uniqueness up to
permutation without supplying Peano authority. Conventional
integer-coefficient Bézout is unavailable in the
natural-only term language, while the four-natural balanced theorem is
checked.

## How to read the status labels

| Label | Meaning |
|---|---|
| `checked_existing` | Already in the original 23-theorem Peano ladder. |
| `checked_m20` | Checked post-baseline extension, including compatible upstream modular entries. |
| `planned_expressible` | Stateable in today's first-order Peano language, but not yet admitted. |
| `blocked_by_language` | Needs a representation/interface not yet implemented as an expanded, checked Peano target. |

The β-coded factorization entries are no longer language-blocked: their exact
expanded first-order formulas have checked certificates at this integration
checkpoint. Primitive list syntax remains absent, and conventional
integer-coefficient Bézout remains a distinct language limitation.

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
6. {doc}`Primes and unique factorization <primes-and-factorization>` explains
   the checked native β-coded FTA and distinguishes it from a primitive-list
   theorem.
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

The previously generated artifact binds the exact statement, dependency list, tactic
script, certificate representation hash, node count, depth, and ordered root
digest
`9650ae53f506c282daf84fca5e9c08d0d48bb36db813b4efc43f54156d25bf6b`.
The authorized runtime integration will regenerate the synchronized artifact
views; this documentation checkpoint does not treat that older root as the
FTA snapshot.
These hashes make drift visible; they do not grant authority.
Authority still comes only from checking the closed proof term against the
closed formula.
