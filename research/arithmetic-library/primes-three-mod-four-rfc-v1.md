# G025 — constructive infinitude of primes congruent to three modulo four

Status: **18 actual independently original-kernel-checked,
dependency-curried proof bodies**, including the complete exact unbounded
three-modulo-four prime theorem. Six previously authored but unadmitted
two-square factor-fold foundations are reused byte-for-byte as necessary
local dependencies; the other twelve progression, decision, finite-search,
Euclid-number, and endpoint proofs are new. Every external dependency already
has checked-use authority in immutable Alpha v22.

This isolated campaign does **not** enroll a theorem, change Alpha v22 or
Stable authority, add an axiom or predicate, assume classical excluded middle,
or silently replace a failed universal statement with an existential witness.
Full Alpha closure requires the separate dependency-closed release admission.

## Exact first-order endpoint

`infinitely_many_primes_three_mod_four` states:

```text
forall B. exists p.
  ((~(p = 1) /\
      forall a b. p = a * b -> a = 1 \/ b = 1) /\
   ((exists gap. gap + S B = p) /\
    (exists k. p = 4 * k + 3)))
```

The actual source uses hygienic generated binder names; the exact statement
SHA-256 is
`3ddac628b2e37925ee3d7a4bd56319de5e173e9065cce6437cab775cc646620b`.
Primality is a nonunit factor-pair condition, strict inequality is witnessed
by `gap + S B = p`, and the residue class is witnessed by `p = 4*k+3`.
Everything expands into the unchanged object language `{0,S,+,*,=}`.

## Conservative shared definition DAG

The candidate contributes three reusable hygienic definition surfaces. Each
rejects non-identifiers, malformed tags, and generated-binder capture. None
introduces parser syntax, a new function symbol, a theorem, or proof
authority.

```text
ModFourThree(n)              := exists k. n = 4*k + 3

PrimeThreeModFourDivisor(n,p) :=
  Prime(p) /\ (ModFourThree(p) /\ Dvd(p,n))

EuclidThreeNumber(c,n)       :=
  exists d. c = S d /\ n = 4*d + 3
```

The direct conceptual edges are:

```text
Prime ────────────────┐
ModFourThree ─────────┼──→ PrimeThreeModFourDivisor
Dvd ──────────────────┘

ModFourThree ────────────→ EuclidThreeNumber
```

Their exact authoring helpers are:

```text
three_mod_four_relation(value, *, tag)
three_mod_four_prime_divisor(dividend, divisor, *, tag)
euclid_three_number(common, value, *, tag)
```

## Constructive finite-search argument

The nontrivial step is not merely saying that a number `3 mod 4` must have a
prime divisor `3 mod 4`: intuitionistically, a contradiction with a universal
property does not by itself produce an existential witness. The actual proof
constructs that witness.

1. The already checked theorem `prime_divides_decidable` decides, for any
   given candidate `p` and dividend `n`, whether `p` is prime and divides
   `n`. If the answer is positive, the checked
   `prime_mod_four_good_or_three` splits `p` constructively into the good
   classes `p=2` or `p=4*k+1`, versus `p=4*k+3`.
2. Good primes are constructively represented as a sum of two squares.
   The checked two-square obstruction excludes simultaneous membership in
   the class `3 mod 4`. Therefore the actual property

   ```text
   Prime(p) /\ ModFourThree(p) /\ Dvd(p,n)
   ```

   is constructively decidable for each concrete pair `(p,n)`.
3. `three_mod_four_prime_divisor_bounded_search` is a genuine kernel-checked
   induction over `B`. It returns either an explicit prime/divisor witness at
   most `B` or a proof excluding every such witness up to `B`.
4. Specialize that search to the bound `n`. Any prime divisor of nonzero `n`
   is at most `n`, by the checked `divisor_le_nonzero`. If the search returns
   no `3 mod 4` prime divisor, all prime divisors of `n` belong to the good
   classes.
5. Six reused factor-fold theorems apply the existing constructive
   beta-coded prime factorization to that positive information. Every decoded
   prime factor is represented by two squares; the explicit finite product of
   those representations is again represented by two squares. Therefore `n`
   would be a sum of two squares.
6. For `n=4*k+3`, this contradicts the independently checked two-square
   obstruction. Hence the finite search must return an actual prime divisor
   `p=4*j+3` together with its divisor quotient. No double-negation
   elimination, Markov principle, unbounded choice, or oracle is used.

The independently checked intermediate theorem is exactly:

```text
forall n.
  (exists k. n = 4*k + 3) ->
  exists p.
    (Prime(p) /\
     ((exists j. p = 4*j + 3) /\
      (exists q. n = p*q))).
```

Its statement SHA-256 is
`6b5d6bcf3910d533b85b9e7e3f020da54ae1910114b1a8f83f0c39e4d3056985`.

## Subtraction-free Euclid construction

Given an arbitrary natural bound `B`, the checked
`bounded_common_multiple_exists` supplies a genuinely nonzero common multiple
`c` of every positive integer at most `B`. The checked `nonzero_is_succ`
supplies `d` such that `c=S d`. Define:

```text
N = 4*d + 3.
```

Thus `N` is `3 mod 4`, and the original successor axioms prove the exact
subtraction-free identity:

```text
N + 1 = 4 * c.
```

The finite-search theorem above returns an actual prime `p=4*k+3` dividing
`N`. Suppose `p<=B`. The existing checked common-multiple theorem then gives
`p|c`, hence `p|4*c`. Since also `p|N`, the checked subtraction-free
`divides_remainder` applied to `4*c = N*1 + 1` gives `p|1`. The existing
`divisor_one` forces `p=1`, contradicting primality. Constructive order
dichotomy therefore returns a genuine strict bound witness `gap + S B = p`.

This closes the previously open G025 root itself. It does not depend on G026
(infinitely many primes congruent to one modulo four), nor does it prove
Dirichlet's theorem for arbitrary arithmetic progressions.

## Independently kernel-checked proof DAG

| Exact theorem | Direct edges | Commands | Kernel nodes | Depth |
| --- | ---: | ---: | ---: | ---: |
| `beta_two_square_prefix_drop_last` | 1 | 16 | 32 | 21 |
| `beta_two_square_prefix_last_represented` | 1 | 12 | 24 | 16 |
| `beta_two_square_represented_factor_product` | 5 | 55 | 106 | 26 |
| `beta_all_prime_entry_is_prime` | 1 | 26 | 42 | 21 |
| `beta_admissible_prime_factor_product_is_two_square` | 2 | 27 | 40 | 21 |
| `positive_number_with_admissible_prime_divisors_is_two_square` | 4 | 47 | 76 | 27 |
| `three_mod_four_progression_nonzero` | 0 | 8 | 21 | 11 |
| `three_mod_four_progression_nonunit` | 0 | 12 | 23 | 11 |
| `three_mod_four_progression_not_two_square` | 1 | 9 | 19 | 12 |
| `three_mod_four_good_prime_exclusive` | 2 | 11 | 23 | 14 |
| `three_mod_four_prime_divisor_decidable` | 3 | 34 | 46 | 14 |
| `three_mod_four_prime_divisor_bounded_search` | 7 | 66 | 92 | 25 |
| `three_mod_four_prime_divisor_exists` | 6 | 46 | 66 | 26 |
| `euclid_three_number_successor_balance` | 0 | 2 | 59 | 16 |
| `euclid_three_progression_prime_exists` | 1 | 5 | 10 | 7 |
| `euclid_three_common_multiple_exclusion` | 5 | 35 | 44 | 23 |
| `euclid_three_prime_divisor_exceeds_bound` | 3 | 29 | 38 | 22 |
| `infinitely_many_primes_three_mod_four` | 4 | 27 | 42 | 20 |

The complete campaign contains **18 new-to-Alpha-v22 theorems**, **46 direct
dependency edges**, **467 actual tactic commands**, **803 kernel proof-body
nodes**, and **793 identity-distinct proof objects**. Its largest individual
proof has **106 nodes**, and maximum depth is **27**. The ordered name
SHA-256 is
`ba74af7579f0e73c4041f0dc58bab86a15f08435ac08f8568cc35417bc37f4b9`.

The external authority surface consists exclusively of existing checked
Alpha-v22 theorem entries:

```text
beta_at_unique
beta_factor_divides_product
beta_product_succ_decompose
beta_product_zero
bounded_common_multiple_contains_bounded_prime
bounded_common_multiple_exists
divides_remainder
divisor_le_nonzero
divisor_one
le_eq_or_lt
le_of_succ_le_succ
le_or_lt
le_refl
le_succ
le_zero
mul_one
multiple_mul_left
nonzero_is_succ
prime_divides_decidable
prime_factorization_existence
prime_mod_four_good_or_three
prime_nonzero
prime_two_or_one_mod_four_is_sum_of_two_squares
three_mod_four_number_not_equal_represented
two_square_representation_multiplicatively_closed
```

The exact isolated factory is
`peano_lab.library.primes_three_mod_four_candidate.make_primes_three_mod_four_candidate_theorems`.
The focused proof, closure, source reuse, trusted-input, strict-order,
generated-binder capture, formula tampering, false-conclusion,
missing-dependency, truncated-proof, and executable-number audit is
`tests/test_primes_three_mod_four_candidate.py`. Concrete numerical
examples illustrate witness computation only; every formal theorem still
reaches the unchanged independent intuitionistic kernel.
