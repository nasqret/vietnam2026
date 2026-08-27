# G010: complete perfect-power profiles and actual root production

This additive ordinary-HA development consumes the frozen shared
`prime_valuation_support_candidate` (20 rows), the frozen squarefree
decomposition candidate (16 rows), and unchanged Alpha v28 (2,764 checked,
Stable 432; catalogue SHA-256
`897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9`).
It changes no historical evidence, kernel, trusted inference or resource cap.

## Exact G010 endpoint

`positive_squarefree_kernel_and_power_profile` proves the blueprint statement:

```text
forall n. n != 0 -> exists r s w.
  Squarefree(r) and n=r*(s*s) and PowerProfile(n,w) and
  forall u v. Squarefree(u) -> n=u*(v*v) -> u=r and v=s.
```

The statement SHA-256 is
`d90dd7d83bf94f698c6fde0134034eed5e89b5bae73c2caf58b6cdc788313949`.
Neither a factorization, exponent profile, gcd, correction, root nor finite
choice oracle is an input premise.

## What the profile really encodes

`PowerProfile(n,w)` has two explicit branches:

- **Unit:** `n=1`, `w=0`, and the actual uniform identity
  `forall k. k!=0 -> Pow(1,k,1)`. This is an unbounded theorem for all positive
  degrees, not a finite sample and not a fictitious positive gcd of an empty
  exponent list.
- **Nonunit:** actual decoded data certify `n!=1`, a genuine distinct-prime
  support of `n`, its positive exponent gcd `g`, and beta-decoded roots for
  every positive divisor of `g`.

The nonunit code contains exactly ten fields in this order:

```text
pb, pc, eb, ec, vb, vc, l, g, rb, rc
```

The first seven are the shared `PrimeValuationSupport` data: distinct primes,
their positive exact valuations, corresponding actual power values and actual
product equal to `n`. The next field is the gcd of the decoded exponent
prefix. The last two are the beta root-table codes. Nine actual historical
doubled-Cantor `Pair` constructors package these ten fields into `w`.

`PrimeExponentPrefixGcd(eb,ec,l,g)` is the ordinary greatest-common-divisor
relation: `g` divides every decoded exponent, and every common divisor divides
`g`. It is not defined by perfect-power degrees. `PerfectPowerRootTable(n,g,rb,rc)`
says that for each positive `k` dividing `g`, an actual entry at beta index
`k` is a natural `r` with an actual `Pow(r,k,n)` trace. Zero and nondivisor
indices may be filled with zero; they assert no root.

All public builders take PA terms in an explicit context and are checked for
capture. The exact definition DAG is:

```text
PowerProfile
  -> Pow                         (uniform unit branch)
  -> PerfectPowerProfileData
       -> PerfectPowerProfileCode -> historical Pair
       -> PrimeValuationSupport   -> BetaAt, Prime, Val, Pow, Product, InjectivePrefix
       -> PrimeExponentPrefixGcd  -> finite common divisor -> BetaAt, Lt, Dvd
       -> PerfectPowerRootTable   -> BetaAt, Dvd, Pow
```

The code, gcd and root-table definitions do not assert the classification
theorem by definition. That theorem is proved separately, for the gcd
**actually decoded from the profile**, in
`perfect_power_profile_data_degree_classification`:

```text
k > 0 -> ((exists r. Pow(r,k,n)) <-> Dvd(k,g)).
```

`perfect_power_profile_data_root_lookup` additionally returns the actual
beta entry, not merely an uncoded existential root.

## Constructive proof route

Necessity follows from the shared exact valuation-of-powers law
`v_p(r^k)=k*v_p(r)`. Positivity of the input and degree proves that its base
is nonzero before this law is used.

For sufficiency, ordinary induction on an explicit upper bound for `n`
removes a full prime-power factor `p^e`. The all-prime divisibility condition
constructs an actual quotient `e=k*t`; ordinary power algebra constructs the
root `p^t`. Every other prime valuation is unchanged on the strictly smaller
cofactor, and the removed prime has cofactor valuation zero. The recursive
root and `p^t` multiply to the required actual root. This proves the root
theorem before any root table is defined as a supplied witness.

Finite induction constructs the gcd of the actual exponent list from
canonical binary gcds. Full prime-support coverage equates divisibility of
the finite list with divisibility of every prime valuation, including zero
valuations at absent primes. A nonempty list of positive exponents forces
the gcd to be nonzero.

Finally, finite decidable degree/divisor tests and beta-prefix extensions
tabulate the already proved roots through index `g`. Every positive divisor
of positive `g` is at most `g`, so this finite table covers all allowed
degrees. Actual Pair constructors package the result. For `n=1`, the separate
uniform identity supplies every positive degree directly.

## Ordered candidate inventory

```text
power_value_eq_transport
power_one_base_value
power_one_base_exists
power_product_construct
power_divisible_exponent_root
positive_power_nonzero_base
positive_power_prime_valuations_divisible
prime_valuation_divisibility_cofactor
prime_valuation_divisible_power_root_bounded
prime_valuation_divisible_power_root_exists
prime_exponent_common_divisor_drop
prime_exponent_common_divisor_successor
prime_exponent_common_divisor_factor
prime_exponent_prefix_gcd_empty
prime_exponent_prefix_gcd_successor
prime_exponent_prefix_gcd_exists
prime_exponent_prefix_gcd_functional
prime_valuation_support_nonempty
prime_valuation_support_exponent_gcd_nonzero
prime_exponent_entry_has_prime_valuation
prime_support_common_divisor_implies_all_valuations
prime_support_all_valuations_implies_common_divisor
prime_support_exponent_gcd_divisor_criterion
prime_support_perfect_power_iff_degree_divides
prime_support_exponent_gcd_roots_available
perfect_power_root_table_prefix_append
perfect_power_root_table_conditional_entry
perfect_power_root_table_prefix_exists
perfect_power_root_table_exists
perfect_power_profile_code_exists
perfect_power_profile_exists
perfect_power_profile_data_degree_classification
perfect_power_profile_data_root_lookup
perfect_power_profile_positive
perfect_power_profile_unit_code
perfect_power_profile_nonunit_decode
positive_squarefree_kernel_and_power_profile
```

There are 37 rows, 91 dependency edges and 1,469 ordinary tactic commands.
Ordered names joined by LF including the final LF have SHA-256
`94aacc5c69cbdf54169e9d16b779dcd403dca5db2b9bdbe65ecb90c1a7a7b80f`.
The profile-existence statement SHA-256 is
`260a2dde81237d922ee7ce66be2baa24460396b2caefd3407d6191881e0649c6`.

## Checked evidence

All 37 dependency-curried bodies pass the unchanged original kernel. The
per-row sums are 2,516 proof-node occurrences and 2,514 distinct objects;
maximum body size is 190 and maximum depth is 60. The full focused suite
passes **292 tests** in 28.52 seconds in a fresh bounded process.

Tests independently assemble the full G010/profile/classification/lookup
ASTs, check exact ordinary-body metrics and dependency order, reject forged
endpoints and captured/malformed term surfaces, and exercise actual historical
Pair and beta encoding on complete numerical support/gcd/root data. Numerical
examples only audit the specification; they confer no proof authority.

Together the three frozen G010 factories comprise 73 rows, 229 dependency
edges and 3,142 ordinary commands. Their 618 focused tests pass. Self-contained
empty-context closure and the independent Lean verification are intentionally
separate non-admitting priority-layer artifacts; body acceptance alone is
not Alpha promotion.
