# Constructive four-square strict-descent bridge RFC v1

Status: isolated, independently checked dependency-curried candidate bodies.
The actual prime modular-seed premise is discharged. Universal Lagrange is
still conditional on one explicit, uniformly strict multiplier-descent
hypothesis; it is not an unconditional theorem in this tranche.

Implementation:
[`four_square_lagrange_bridge_candidate.py`](../../peano-lab/py/peano_lab/library/four_square_lagrange_bridge_candidate.py).
Focused audit:
[`test_four_square_lagrange_bridge_candidate.py`](../../peano-lab/py/tests/test_four_square_lagrange_bridge_candidate.py).

## Exact mathematical boundary

The already checked residue-intersection endpoint proves

```text
forall p. Prime(p) -> exists a b k. a²+b²+1 = p*k.
```

Every such seed has a nonzero multiplier and directly represents `p*k` by the
four natural coordinates `(a,b,1,0)`. The checked strong-induction descent
then proves

```text
four_square_prime_from_strict_descent:

  StrictPrimeMultipleDescent
    -> forall p. Prime(p) -> exists a b c d. p = a²+b²+c²+d².

SHA-256: a0db9304ae96fb7094a9722321341b08818fdf0514b9534ec6a81b8340561809
```

The checked prime-factor reduction and unconditional Euler multiplicative
identity subsequently give

```text
four_square_lagrange_from_strict_descent:

  StrictPrimeMultipleDescent
    -> forall n. exists a b c d. n = a²+b²+c²+d².

SHA-256: 9f7dff900d6c44b4dc8eed887ea9b29811d79882645ba7d2264f60765c503dea
```

Here `StrictPrimeMultipleDescent` expands conservatively to the actual
first-order requirement: every represented nonzero prime multiple with
multiplier different from one admits a represented nonzero strictly smaller
multiplier. Neither checked formula assumes prime seeds, classical reasoning,
or hidden representation premises. The strict-descent antecedent remains
visible and is not represented as an established unconditional theorem.

## Sharp bounded-multiplier invariant

Centered quaternion descent must retain its classical sharp invariant
`0 < k < p`: without `k < p`, all centered residues may vanish, so an
unrestricted strict step is not obtained merely from centered remainders.
The separate checked roots

```text
four_square_descent_below_prime_multiplier_bounded
four_square_prime_from_bounded_strict_descent_and_seed
four_square_prime_from_bounded_strict_descent
four_square_lagrange_from_bounded_strict_descent
```

therefore formulate strict descent only for represented prime multiples
strictly below their prime. Bounded natural induction preserves `r < k < p`
by constructive transitivity, terminates at multiplier one, and constructs
the prime representation from any actual seed whose multiplier is strictly
below the prime. The independently checked unconditional
`four_square_prime_bounded_modular_seed` supplies exactly such a seed for
every prime, so the final conditional Lagrange root retains only the precise
below-prime strict-step hypothesis:

```text
four_square_lagrange_from_bounded_strict_descent

SHA-256: 1c950fd851415f84bc19ab5370d15465211e4cfcb280ae2594cef84bf5c47ed1
```

This weaker antecedent is explicit; no stronger unrestricted descent
assumption is silently substituted.

All notation expands into the unchanged language `{0,S,+,*,=}`. Sealed Alpha
and Stable membership remain unchanged.
