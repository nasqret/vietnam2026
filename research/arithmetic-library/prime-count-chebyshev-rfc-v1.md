# Exact constructive Chebyshev bounds

This additive candidate proves the full stated G027 inequalities over the
unchanged intuitionistic Peano kernel. The immutable parent is Alpha v26:
2,138 checked-use theorems, unchanged Stable432, catalogue SHA-256
`969c261f924060552dda393427b4fbc51515b9d4e69daa17f5e9f1691b5ab534`.

## Exact statement and definitions

```
forall N ell k.
  2 <= N -> BitLen(N,ell) -> PrimeCount(N,k) ->
  N <= 8*k*ell /\ k*ell <= 8*N.
```

There is no supplied factorization, valuation, analytic estimate, primorial,
power, central binomial coefficient, or cutoff count among its premises.
Those objects are constructed internally from the existing total relations.
The constants are exactly the blueprint's eight on each side, not unspecified
asymptotic constants. The existing `BitLen(0,1)` convention is unchanged.

`PrimeBitPrefix(b,c,N)` has an actual beta entry at each index `i<N`, equal to
one when `S i` is prime and to zero when it is not. `PrimeCount(N,k)` supplies
that entire mask and an actual finite sum equal to `k`. Thus it counts exactly
the primes at most N. The mask is constructed using primality decidability
and beta extension, with no finite-choice oracle. Count totality, uniqueness,
the values at zero and one, the bound `k<=N`, and positivity for `N>=2` are
separately proved. Count uniqueness is independent of the chosen beta codes.

`CutoffBitPrefix(U,b,c,d,f,N)` copies the source mask at indices at least U
and stores zero below U. Since mask index i represents the integer S i,
this counts exactly the primes strictly greater than U. It is independently
constructed and its actual count L satisfies `k<=U+L`.

All three public definitions are hygienic first-order expansions. No parser
symbol, trusted function, kernel axiom, or classical rule is added. Internal
bit-weighted product predicates likewise expand to exact beta entries and
ordinary arithmetic comparisons; they are not numerical estimators.

## Proof of the lower bound

For `N>=8`, construct `N=h+h+d`, with an actual bit d and `h>=4`. Construct
the actual central binomial coefficient C and binary power V=2^h. The earlier
exact central-binomial lower bound, together with the newly proved
`h+1<=2^h`, gives `V<=C` by constructive multiplication cancellation.

The existing complete prime-contribution product reconstructs C over the
entire prefix through N. At nonprime positions its factor is one; at each
prime position its actual prime-power contribution is at most 2h, by the
checked binary-carry theorem. Induction on product length proves the general
bit-weighted bound and therefore `C<=(2h)^k`. BitLen supplies an actual upper
power W=2^ell>N. Power monotonicity, multiplication of exponents, and order
reflection for binary powers give `h<=ell*k`. Elementary witnessed order then
gives the stated `N<=8*k*ell`. For `2<=N<8`, the actual prime two and positive
binary length supply the required small boundary bound.

## Proof of the upper bound

For `ell<=4`, use `k<=N`. Otherwise write the lower binary exponent as
`ell-1=h+h+d` with h at least two, and construct U=2^h. The exact lower power
from BitLen gives `U*U<=N`. The proof also establishes `ell<=2U` and
`ell<=3h`; no real logarithm or square-root approximation occurs.

Construct the cutoff mask and its count L. A second product-length induction
gives `U^L<=Primorial(N)`, since every selected prime is greater than U and
every other dense factor is at least one. The inherited exact primorial
bound `Primorial(N)<=4^N`, with genuine power identities and order reflection,
gives `h*L<=2N`. Now:

```
k*ell <= (U+L)*ell
       = U*ell + L*ell
       <= 2N + 6N = 8N.
```

These are actual proof dependencies from the Bertrand infrastructure. The
final strict-Bertrand theorem or its finite-chain corollary is not inserted
as a fictitious proof edge: this route directly uses the stronger checked
central-binomial and primorial estimates underlying that campaign.

## Candidate checks and admission boundary

The 55 dependency-curried bodies all pass the original kernel: 239 direct
edges, 2,621 authored tactic commands, 4,755 proof-node occurrences, maximum
297 nodes per body and depth64. Ordered names SHA-256:
`ae973727c4ad4e3157e353a19d4d4c2c2dacca967d154f83914bf8ebc813e9fb`.
Exact full-root statement SHA-256:
`38a80957c2e9e9545cf57e1a036768d506a64edd891be2d0125ffd499fab7428`.

All 429 focused tests pass. They check the exact root's three premises and both constants,
all body metrics, dependency order, altered conclusions, truncated scripts,
every missing dependency, hygienic definitions, and numerical boundaries up
to 10,000, including power thresholds, zero bases, and empty products. Numeric
tests illustrate the formal theorems; they do not stand in for them.

These are candidate-body receipts, not Alpha admission or independent Lean
acceptance. The pinned parent catalogue supplies only authoring hypotheses.
The complete actual dependency cone must still be reconstructed, checked by
the unchanged kernel, and accepted by the compiled independent Lean verifier
before any checked-use or campaign-completion status changes.
