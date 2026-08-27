# G010: a unique constructive squarefree kernel

This is an additive ordinary-HA candidate over unchanged Alpha v28
(`897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9`,
2,764 checked theorems, Stable 432). No kernel, trusted tactic, historical
proof source, resource cap, edition or publication is changed.

## Exact definitions and endpoint

`Squarefree(n)` is precisely the blueprint's bounded definition:

```text
n != 0 and forall p. Prime(p) -> p <= n -> not Dvd(p*p,n).
```

It is not defined by the existence or uniqueness of a squarefree
decomposition. `SquarefreeDecomposition(n,r,s)` is just `Squarefree(r)`
together with the literal equality `n=r*(s*s)`.

`squarefree_decomposition_exists_unique` proves:

```text
forall n. n != 0 -> exists r s.
  SquarefreeDecomposition(n,r,s) and
  forall u v. SquarefreeDecomposition(n,u,v) -> u=r and v=s.
```

Thus both natural outputs are literally unique. The theorem includes `n=1`,
where the unique pair is `(1,1)`. Zero is excluded by the input premise and
by the squarefree predicate. There is no sign ambiguity over naturals.

Public builders accept arbitrary PA terms with an explicit variable context,
reject capture, and preserve the existing double-and-add representation of
large numerals. The definition DAG is small and exact:
`Squarefree -> Prime, Le, Dvd`; `SquarefreeDecomposition -> Squarefree` plus
ordinary multiplication and equality. Global registry insertion is deferred
to the additive release owner.

## Genuine existence and uniqueness proofs

Finite natural induction decides whether a prime square divides the input
below any specified bound, or constructs such a prime and an actual quotient.
Taking the bound `n+1` gives either squarefreeness or a squared prime divisor.
A squared divisor cannot escape the bounded definition: its base prime is
itself a divisor of the positive input, hence is at most the input.

If `n=p*p*u`, the prime square is not one and `u<n`. Ordinary induction on
an explicit upper bound recursively decomposes `u`; multiplication of the
constructed square root by `p` restores the original value. No maximal-square
factor, factoring oracle, root oracle or strong-induction inference is assumed.

For uniqueness, every squared divisor of a squarefree natural has root one:
a nonunit root would itself have a prime divisor, contradicting squarefreeness.
Given two decompositions, the existing canonical gcd reduces their square
roots to coprime quotients. Cancellation of the common nonzero square and
Gauss's coprime cancellation force both quotients to be one. Both kernels
and both original roots then agree.

## Ordered candidate inventory

```text
divides_square_of_divides
squarefree_excludes_prime_square
prime_square_ne_one
squarefree_squared_divisor_is_one
coprime_squared_pair
squarefree_coprime_square_factor_is_one
squarefree_square_factor_reassociate
nonzero_square_factor_root
bounded_prime_square_divisor_search
squarefree_or_prime_square_divisor
squarefree_decomposition_bounded_exists
squarefree_decomposition_exists
squarefree_one
squarefree_coprime_square_balance
squarefree_decomposition_functional
squarefree_decomposition_exists_unique
```

The factory has 16 rows, 57 dependency edges and 551 ordinary tactic commands.
Ordered names joined by LF including the final LF have SHA-256
`79a9ccb662b7b3fb8b89b2a147778518dbef9db2c3fd27b580dbb87385a8d089`.
The final endpoint statement SHA-256 is
`efce5f0c441fd9d953dceab7c4a0869a11c41ad65e4eee3d1e73e3c6b92aacf3`.

## Checked evidence and limits

All 16 dependency-curried bodies pass the unchanged original kernel. Their
per-row sums are 1,175 proof-node occurrences and 1,164 distinct proof objects;
maximum body size is 369 and maximum depth is 48. The complete focused suite
passes **175 tests** in 1.89 seconds in a fresh bounded process.

The tests include independently assembled definition and endpoint ASTs,
literal body-metric pins, ordinary dependency order, malformed and capture
rejection, compound/large-term surfaces, poisoned endpoints, and exhaustive
small positive examples checking uniqueness. Numerical examples are a
specification audit, not formal proof authority. Dependency-curried acceptance
is not Alpha admission: self-contained dependency closure and independent
Lean checking are performed separately by the non-admitting priority-layer
bundle campaign.
