# G026 — constructive infinitude of primes congruent to one modulo four

Status: **ten actual independently kernel-checked dependency-curried proof
bodies**, including the complete exact unbounded-prime endpoint. All external
prerequisites already have checked-use authority in immutable Alpha v18. This
isolated candidate does not enroll or promote any theorem, change Stable or
Alpha authority, assume infinitely many primes congruent to three modulo four,
or introduce an arithmetic oracle, axiom, proof rule, or classical principle.

## Exact first-order theorem

The final theorem `infinitely_many_primes_one_mod_four` states:

```text
forall B. exists p.
  ((~(p = 1) /\
      forall a b. p = a * b -> a = 1 \/ b = 1) /\
   ((exists gap. gap + S B = p) /\
    (exists k. p = 4 * k + 1)))
```

The actual canonical source uses hygienic generated names for the local prime
factor and residue binders. Its exact statement SHA-256 is
`eb4e068b6bb3a271118a6e6aaea03ddd9d0fc10317f38bc4697b0a46dd9ac1be`.
Every relation is expanded into the unchanged first-order language
`{0, S, +, *, =}`. Strict inequality is an explicit witness
`gap + S B = p`; primality is an explicit nonunit factor-pair condition;
and the one-modulo-four class is the explicit equation `p = 4*k+1`.

## Constructive Euclid argument

For an arbitrary natural bound `B`, the already Stable-closed theorem
`bounded_common_multiple_exists` returns an explicitly nonzero natural `c`
divisible by every positive natural at most `B`. Consider

```text
N = (2*c) * (2*c) + 1 = 4*c*c + 1.
```

1. The original Peano successor axioms prove `N != 0`. Since `c != 0`, the
   checked multiplication-zero theorem also proves `N != 1`. The already
   Stable-closed `prime_divisor_exists` therefore returns an actual prime `p`
   and an actual quotient witnessing `N = p*q`.
2. `N` is odd: its square block has the witnessed even form
   `2 * (c * (2*c))`, so the prime divisor cannot be `2`.
3. The already Alpha-closed exact theorem
   `three_mod_four_prime_divides_two_square_norm_divides_both` says that a
   three-modulo-four prime dividing `a*a+b*b` divides both `a` and `b`.
   Apply it with `a = 2*c` and `b = 1`: any three-modulo-four prime divisor
   of `N` would divide `1`, contradicting its nonunit primality. The already
   checked `prime_mod_four_trichotomy` now leaves only a witnessed residue
   `p = 4*k+1`.
4. If `p <= B`, the common-multiple property gives a quotient witnessing
   `p | c`. Existing constructive divisibility multiplication therefore gives
   `p | (2*c)*(2*c)`. Since also `p | N`, the already Stable-closed theorem
   `divides_remainder` gives `p | 1`, again contradicting primality. The
   constructive order dichotomy `le_or_lt` consequently returns a genuine
   witness `gap + S B = p`.

This direct proof has no mathematical prerequisite on G025 (infinitely many
primes congruent to three modulo four). The previous campaign edge G025 → G026
was an unnecessarily restrictive planning edge; quadratic-reciprocity/two-
square obstruction and the checked common-multiple substrate suffice.

## Independently checked proof microsteps

| Exact candidate theorem | Direct dependencies | Commands | Kernel proof nodes | Depth |
| --- | ---: | ---: | ---: | ---: |
| `doubled_square_plus_one_nonzero` | 0 | 6 | 19 | 9 |
| `doubled_square_plus_one_nonunit` | 1 | 27 | 35 | 14 |
| `doubled_square_plus_one_has_prime_divisor` | 3 | 11 | 27 | 14 |
| `doubled_square_plus_one_not_divisible_by_two` | 2 | 13 | 18 | 11 |
| `three_mod_four_prime_cannot_divide_doubled_square_plus_one` | 3 | 29 | 33 | 18 |
| `prime_divisor_of_doubled_square_plus_one_is_one_mod_four` | 3 | 25 | 35 | 16 |
| `bounded_common_multiple_contains_bounded_prime` | 3 | 32 | 42 | 20 |
| `common_multiple_prime_cannot_divide_doubled_square_plus_one` | 5 | 36 | 42 | 21 |
| `doubled_square_prime_divisor_exceeds_common_multiple_bound` | 3 | 25 | 33 | 20 |
| `infinitely_many_primes_one_mod_four` | 4 | 26 | 41 | 17 |

The complete candidate stack has **ten theorems**, **27 exact direct
dependency edges**, **230 actual tactic commands**, and **325 checked kernel
proof-body nodes**. Its largest individual proof has **42 nodes**, **42 proof
objects**, and depth **21**. The ordered theorem-name SHA-256 is
`80d387e5567f93e1a56014555257e14193f42b3de56da6bae354d55fc792220c`.

The only external arithmetic inputs are already checked Alpha-v18 theorems:

```text
add_comm
bounded_common_multiple_exists
divides_remainder
divisor_one
even_odd_exclusive_pointwise
le_or_lt
mul_assoc
mul_eq_zero
mul_one
multiple_mul_left
multiple_mul_right
nonzero_is_succ
prime_divisor_exists
prime_mod_four_trichotomy
prime_nonzero
three_mod_four_prime_divides_two_square_norm_divides_both
```

The exact source factory is
`peano_lab.library.primes_one_mod_four_candidate.make_primes_one_mod_four_candidate_theorems`.
The focused proof, exact-formula, source-order, witness-bound, trusted-input,
false-conclusion, truncated-script, missing-dependency, and numeric-example
audit is `tests/test_primes_one_mod_four_candidate.py`; all **41** tests pass.
Numeric examples illustrate witness computation only and never replace the
unchanged independent intuitionistic kernel.
