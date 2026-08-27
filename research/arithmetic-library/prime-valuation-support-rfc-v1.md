# Prime valuation powers and genuine finite support

This additive prerequisite is shared by G010 (squarefree kernels and perfect
powers), G006 (totients), and G036 (LTE). It does not depend on any of those
endpoints and changes no historical library, kernel, trusted tactic or bound.

The parent is the unchanged Alpha-v28 catalogue, SHA-256
`897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9`,
with 2,764 checked theorems and the same 432 Stable members. Tests reconstruct
its theorem statements and ordinary bodies in a small table. That table is
only the hypothesis basis for dependency-curried candidate-body checking;
its hash is not proof authority. Empty-context closure and the independent
Lean bundle belong to the later additive release campaign.

## Exact mathematical interfaces

`prime_power_valuation_pow` proves, for a prime `p`, positive `a`, its actual
bounded maximal valuation `e`, and an actual `Pow(a,k,z)` trace:

```text
Val(p,a,e) -> Pow(a,k,z) -> Val(p,z,k*e).
```

The prime and nonzero guards are explicit in the full statement. The exponent
`k` may be zero. The companion `prime_power_valuation_pow_value` identifies
any supplied output valuation with `k*e`; the constructive version also
produces the output valuation graph. Ordinary induction on `k` uses the
existing successor power decomposition and valuation product law.

`PrimeValuationSupport(n,pb,pc,eb,ec,vb,vc,l)` has exactly eight arguments and
expands to these five right-associated conjuncts:

1. `n != 0`.
2. The actual beta prefix `(pb,pc)` of length `l` is injective.
3. Every index below `l` has actual entries `p,e,v` in the three beta prefixes,
   with `Prime(p)`, `e != 0`, `Val(p,n,e)`, and `Pow(p,e,v)`.
4. Every prime divisor of `n` occurs at an actual index below `l` in the prime
   prefix.
5. The actual finite product trace `Product(vb,vc,l,n)` holds.

These conditions are not a list supplied as an assumption to the public
existence theorem. `prime_valuation_support_exists` proves:

```text
forall n. n != 0 -> exists pb pc eb ec vb vc l.
  PrimeValuationSupport(n,pb,pc,eb,ec,vb,vc,l).
```

For `n=1` all three prefixes have length zero and their product is one.
There is no dummy prime or positive valuation at the unit boundary. Zero is
outside the positive theorem, not assigned an artificial prime support.

## Construction and definition DAG

The support builders reuse the exact historical `BetaAt`, `Product`, `Pow`,
bounded valuation, and injective-prefix expansions. Public builders parse
every argument as a PA term in an explicit distinct-variable context and
reject binder capture. Compound terms and large double-and-add numerals are
included in the tests. No definition is a new kernel rule.

The actual proof dependencies proceed as follows:

```text
Pow successor + Val product
          -> Val(Pow) -> distinct-prime powers have valuation zero
          -> old valuations survive restoring a removed prime power

prime divisor existence + exact valuation cofactor
          -> n = p^e*u, e>0, p does not divide u, and u<n

beta prefix extension + actual product extension + entry transport
          -> append a fresh full prime power, preserving distinctness

empty support of 1 + strict cofactor + append
          -> ordinary bounded induction -> unrestricted positive support
```

At each recursion step, the full power is removed, so its prime does not
divide the cofactor. Every old support prime divides that cofactor; it is
therefore genuinely different from the newly appended prime. Euclid's
prime-product lemma and the prime-power divisor classification prove that
the resulting prefix covers every prime divisor of the input. Three actual
beta extensions construct the codes, and the product trace is extended with
the actual power value. No factoring, root, finite-choice or sorting oracle
is introduced.

## Candidate inventory and validation

The factory `make_prime_valuation_support_candidate_theorems` returns 20 rows
in dependency order, with 81 declared dependency edges and 1,122 ordinary
tactic commands. Ordered names joined by LF, including a final LF, have
SHA-256 `ad2e3ab0bd8d0dc899c41927629e67b5551aed6e48333565c78a4d1bb7a601af`.

All 20 dependency-curried bodies have been accepted by the unchanged original
kernel: 1,767 proof-node occurrences and 1,765 distinct proof objects summed
per row, maximum body size 358 and maximum depth 73. The largest body is the
full three-prefix append; the unrestricted public support root has 21 nodes
and depth 12. Checks use fresh bounded processes, not increased proof or
search caps.

The focused suite contains the 20 body replays and 131 additional tests:
independently assembled endpoint ASTs, exact non-oracular support structure,
dependency order and ordinary command checks, hygienic compound/large-term
surfaces, poisoned-endpoint rejection, and independent numerical boundary
examples. Numerical examples are specification checks, not formal evidence.

The support root statement SHA-256 is
`d6e0d6a185004dcf15dae72c0bc893200f0b3d5688a8784c53497ef8fe60907b`.
This module alone does not claim squarefree uniqueness, perfect-power
classification, Euler's product or LTE; it supplies their shared genuine
prime-exponent data.
