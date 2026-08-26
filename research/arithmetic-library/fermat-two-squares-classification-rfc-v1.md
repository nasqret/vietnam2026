# Constructive two-square classification: multiplication and prime obstruction

The isolated classification factory currently contributes **20 independently
kernel-checked, dependency-curried first-order HA proof bodies**.  It proves
the exact Brahmagupta–Fibonacci multiplication identity, existential
multiplicative closure, the classical prime-divisor obstruction, and the
complete prime-level representation equivalence.  This factory alone is
**not a complete all-integer classification**; the separate constructive
pairing-and-descent factory now proves the full nonzero and zero-inclusive
all-natural valuation criteria from these checked prerequisites.
Every candidate is **not enrolled in Alpha** and none is promoted to Stable.

## 1. Explicit, subtraction-free multiplication

For natural coordinates `a,b,c,d`, constructive totality of natural order
provides a witness `m` satisfying at least one ordinary sign branch (both
branches agree when `m = 0`):

```text
a*d = b*c + m  or  b*c = a*d + m.
```

The independently checked endpoint is

```text
brahmagupta_fibonacci_two_square_identity:
  forall a b c d m.
    (a*d = b*c+m or b*c = a*d+m) ->
    (a*a+b*b)*(c*c+d*d) = (a*c+b*d)*(a*c+b*d) + m*m.
```

Its SHA-256 statement identity is
`9131766952969d2d05e170ce8bcd4cff48b629848c0ccb9eb5665cbe6ee770a7`.
The proof has six explicit dependencies, **53 proof nodes**, and proof
depth **23**.  No subtraction primitive, signed axiom, ring oracle, or
classical excluded middle is introduced.

The subsequent theorem
`two_square_representation_multiplicatively_closed` takes actual existential
representations of `u` and `v` and returns the concrete witnesses

```text
x = a*c + b*d,
y = |a*d-b*c|,
u*v = x*x + y*y.
```

Absolute value here means the explicitly witnessed natural sign disjunction,
not a new term or trusted operation.  Its statement SHA-256 is
`8e82cb5f76a2148032c1bce4e4a3a5b2d763af8cd26dd91d09512a7ad11b6e9f`.

## 2. The exact prime obstruction

The second flagship is

```text
three_mod_four_prime_divides_two_square_norm_divides_both:
  forall p a b.
    Prime(p) ->
    (exists t. p = 4*t+3) ->
    (exists k. a*a+b*b = p*k) ->
      (exists u. a = p*u) and (exists v. b = p*v).
```

Its SHA-256 statement identity is
`042e2ab7c4566a661204e54f8945e4101fec83bcec12f2614293917528f3fa7c`.
The final body has four dependencies, **55 proof nodes**, and proof depth
**21**.

The constructive argument is fully exposed:

1. `prime_coprime_or_divides` decides the coordinate into its coprime or
   explicitly divisible branch.
2. In the coprime branch `prime_mod_inverse` constructs a witnessed modular
   inverse `z` for that coordinate.
3. Balanced congruence transports `p | a*a+b*b` through multiplication by
   `z*z`, giving the actual witnessed divisibility
   `p | (a*z)*(a*z)+1`.
4. For `p = S n`, explicit balanced witnesses turn this divisibility into
   `QRes(p,n)`: the predecessor represents `-1` modulo `p`.
5. The already checked first supplementary law excludes that residue for
   `p = 3 mod 4`; therefore the coprime branch is impossible.
6. Apply the argument again after swapping the two norm coordinates.

All relations expand into the original language `{0,S,+,*,=}`.  In
particular, `Prime`, congruence, divisibility, and quadratic residue are
display abbreviations, not new trusted predicates.

## 3. Complete prime-level classification

The new constructive prime trichotomy establishes

```text
Prime(p) -> p = 2 or p = 1 mod 4 or p = 3 mod 4.
```

Combined with the existing prime two-square representation theorem and the
elementary modulo-four obstruction, it gives the exact iff

```text
prime_is_two_squares_iff_two_or_one_mod_four:
  forall p.
    Prime(p) ->
      ((exists x y. p = x*x+y*y) <->
       (p = 2 or exists k. p = 4*k+1)).
```

The statement SHA-256 is
`84184c6c9fccba3457f8db4cb5716f0e75e85fa2749f1db6471f902cbbe415d7`.
Its dependency-curried proof has **122 nodes**, proof depth **25**, and
returns actual representing coordinates in its constructive direction.

## 4. Zero and small boundaries

Separate checked candidates provide the concrete representations

```text
0 = 0²+0²,
1 = 1²+0²,
2 = 1²+1²,
n² = n²+0².
```

The eventual valuation criterion must quantify over **positive** `n`; the
zero case has its own representation because finite `p`-adic valuation of
zero is not defined by the current exact-cofactor interface.

## 5. Completed all-natural classification and separate release gates

The complete target is still

```text
forall n > 0.
  (exists x y. n = x*x+y*y)
  <->
  forall p e.
    Prime(p) -> p = 3 mod 4 -> PowerValuation(p,n,e) -> Even(e).
```

The independent valuation tranche has now proved the complete forward
implication: every nonzero represented natural has even valuation at each
prime congruent to three modulo four. Its exact endpoint is

```text
three_mod_four_prime_represented_nonzero_valuation_even
```

with statement SHA-256
`9d34484a80443e77d136106cf009c3ba5604cac269d9937d5b20056a3171a877`.
The separate factor-fold tranche also constructs representations from
individually represented factors, admissible prime products, and grouped
equal prime-square blocks.

The independent pairing-and-descent tranche has now completed the converse
without needing to iterate a beta-coded factorization at all. Ordinary
bounded induction on the natural value chooses an actual prime divisor. A
prime equal to two or one modulo four is itself represented and is removed
as a singleton; a prime equal to three modulo four and having even valuation
is removed as an explicitly witnessed square factor. In both cases the
smaller nonzero quotient inherits the complete universally quantified
even-valuation invariant, and the induction hypothesis supplies actual
representing coordinates.

The exact completed nonzero theorem is

```text
nonzero_two_square_iff_even_three_mod_four_prime_valuations
```

with statement SHA-256
`025b1283e41d88b9def44672ffdd033d1055b84ccf43bc6af06c093dc90dceac`.
The final all-natural theorem is

```text
two_square_iff_zero_or_even_three_mod_four_prime_valuations
```

with statement SHA-256
`4c39da833a313bab5ae810215dae5bbc9cc78ea951fe97fb177c36a5347cecd5`.
Zero is explicitly separated from the nonzero valuation domain; no
undefined finite valuation of zero is assumed. Both flagships are complete
intuitionistic mathematical proofs at the dependency-curried candidate-body
layer, not Alpha or Stable theorem admissions.

Focused verification:

```bash
cd peano-lab/py
python3 -m pytest -q --tb=line \
  tests/test_fermat_two_squares_classification_candidate.py
```

Independent empty-context closure, cold replay, Alpha admission, Stable
promotion, and remote publication all remain separate gates.
