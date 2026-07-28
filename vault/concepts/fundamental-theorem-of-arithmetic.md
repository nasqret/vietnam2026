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
nonunit natural.

FTA itself is **not** proved in native Peano Lab. The direct list-oriented
existence, uniqueness, and combined catalog endpoints remain
`blocked_by_language`; the selected conservative route must first replace that
surface representation with fully expanded β-coded formulas. Its remaining
critical path is greatest-prime-divisor descent, β-value functionality,
binary and bounded CRT, finite-prefix extension/restriction, prefix-product
trace existence and composition, finite-product Euclid/cancellation, and the
final existence and extensional-uniqueness descents. Accordingly no Peano FTA
is exposed through `pa lib`.

The repository now also contains an independently checked Lean 4 companion.
It proves that every nonzero natural has a finite list of prime factors and
that any other such list is a permutation. Its pinned audit rejects `sorryAx`
and records the exact standard axioms `propext`, `Classical.choice`, and
`Quot.sound`. It fixes the mathematical endpoint without acting as a Peano
axiom.

## Related

[[arithmetic-library-moc]] · [[prime-number]] · [[lemma-dependency-dag]] ·
[[trusted-kernel]] · [[godel-beta-sequence]] · [[prime_divisor_exists]] ·
[[euclid_prime_dvd_product]]
