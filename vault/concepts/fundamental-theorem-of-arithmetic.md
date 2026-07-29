---
title: Fundamental Theorem of Arithmetic
tags: [number-theory, factorization, prime, language-boundary]
---

The **Fundamental Theorem of Arithmetic** has two parts: every natural greater
than one is a finite product of primes, and that product is unique up to
reordering, with multiplicities preserved. The chosen Peano and Lean endpoints
extend this to every nonzero natural: one has the empty factorization.

Strong induction and prime-divisor existence support existence;
[[euclids-lemma]] supports uniqueness. The present Peano term language has no
primitive finite lists, multisets, exponent maps, or products.

The representation review selected a conservative [[godel-beta-sequence]]:
natural codes represent factors and a second code represents prefix products.
Sorted decoded entries make uniqueness extensional without equating
non-unique codes. The encoding itself adds no kernel rule: every relation must
expand into the existing PA object language. Division existence
and uniqueness and constructive [[gcd_exists_relational|relational gcd
existence]] are now checked. Balanced Bézout, [[gauss_coprime_cancel]], and
[[euclids-lemma]] are checked as well. The existence-side arithmetic entrance
is now checked too: [[prime_or_composite]], [[proper_factor_lt]], and
[[prime_divisor_exists]] give a constructive prime divisor of every nonzero
nonunit natural. Single-position β decoding is now checked as well:
[[beta_at_exists]] and [[beta_at_unique]] establish totality and functionality
of the expanded `At` relation, while [[beta_at_to_mod_eq]] connects it to the
checked congruence API and [[beta_at_of_mod_eq_bound]] supplies the bounded
reverse direction. [[binary_crt]] now proves constructive binary CRT for
arbitrary residues and positive coprime natural moduli, and
[[binary_crt_beta_pair]] constructs one code realizing two bounded β values.
That specialization assumes, rather than proves, coprimality of its two β
moduli. The subsequent [[beta_moduli_coprime_of_gap_dvd]] proves the needed
coprimality when the ordered index gap divides `c`, and
[[binary_crt_beta_pair_of_gap_dvd]] uses it directly.
[[bounded_common_multiple_exists]] constructs a nonzero `c` divisible
by every positive natural through a fixed bound.

These statements do not imply unconditional pairwise β-modulus coprimality,
which is false: `c=1` at indices 1 and 4 yields moduli 3 and 6.

The finite-bound version is now checked:
[[beta_moduli_pairwise_coprime_bounded]] and
[[bounded_beta_moduli_pairwise_coprime_exists]] produce a suitable base with
pairwise-coprime moduli throughout one bounded prefix.
[[coprime_mul_left]], [[coprime_mul_right]],
[[mod_eq_of_mod_eq_multiple]], and [[binary_crt_fold_step]] establish the
product-coprimality, modulus-descent, and one-step CRT algebra needed by an
iteration.
[[beta_accumulated_product_step]], [[beta_crt_prefix_congruence_step]], and
[[beta_crt_prefix_invariant_step]] advance the combined invariant, while
[[bounded_beta_crt_prefix_invariant]] folds it by ordinary induction.
[[bounded_beta_crt_for_existing_code]] starts from values already decoded from
a supplied `BetaAt` code. It therefore does not establish coding for an
arbitrary finite sequence.

The later native tranche closes those former encoding gates: finite-prefix
recoding and append, exact β-coded prefix-product traces, Product existence and
functionality, greatest-prime-divisor descent, canonical append, strengthened
factorization existence, and sorted last-factor uniqueness are all checked.

At this integration checkpoint the exact endpoints are:

| Endpoint | Nodes | Depth | Cuts |
|---|---:|---:|---:|
| `prime_factorization_existence` | 43,973 | 98 | 1,328 |
| `prime_factorization_uniqueness` | 29,789 | 82 | 854 |
| `fundamental_theorem_of_arithmetic` | 73,767 | 99 | 2,184 |

The FTA certificate SHA-256 is
`fd978f59bf3b0aa7b6c9ec1bc92ab5e7bbf949c25309173e098bd8f3b8de0958`.
It passes independent empty-context checking and the full prove/use/exact/QED
path under the 100,000-node/depth-256 live/use cap. It uses only PA1–PA6 and
induction and contains no DNE. Dependency, hypothesis, PA-rule, and semantic
mutation audits are live. Runtime integration is complete.

This is a native β-coded FTA, not a primitive-list theorem. Peano Lab still
has no list or multiset type. Since multiple codes may decode the same prefix,
uniqueness proves equal lengths and equality of every decoded bounded entry;
it does not assert raw-code equality. The independently checked
[[constructive-prime-unboundedness|prime-unboundedness theorem]] is not needed
for this theorem. Conventional integer-coefficient Bézout remains
unavailable in the natural-only language, while balanced four-natural Bézout
is checked.

The repository also contains an independently checked Lean 4 companion.
It proves that every nonzero natural has a finite list of prime factors and
that any other such list is a permutation. Its pinned audit rejects `sorryAx`
and records the exact standard axioms `propext`, `Classical.choice`, and
`Quot.sound`. It proves the conventional list/permutation presentation without
acting as a Peano axiom or supplying any part of the native certificate.

## Related

[[arithmetic-library-moc]] · [[prime-number]] · [[lemma-dependency-dag]] ·
[[trusted-kernel]] · [[godel-beta-sequence]] · [[prime_divisor_exists]] ·
[[euclid_prime_dvd_product]] · [[binary_crt]] ·
[[binary_crt_beta_pair_of_gap_dvd]] ·
[[bounded_beta_moduli_pairwise_coprime_exists]] · [[binary_crt_fold_step]] ·
[[bounded_beta_crt_for_existing_code]]
