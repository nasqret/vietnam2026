# RFC HA-R6-BERTRAND-FACTOR-1: central prime-divisor support

**Status:** binding subordinate statement, dependency, evidence, trust,
capacity, and release contract; this document grants no theorem authority

**Parent campaign:**
[`RFC HA-R6-BERTRAND-1`](ha-bertrand-postulate-campaign-rfc-v1.md), SHA-256
`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`

**Representation amendment:**
[`RFC HA-R6-BERTRAND-2`](ha-bertrand-postulate-campaign-rfc-v2.md), SHA-256
`af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`

**Immutable edition parent:** Alpha v10 at commit
`1888aef98eb8cb6e421122e165ed938f7d5e03ef`

**Candidate parent:** commit
`7539b448ee43076d3960f4d4f6724044f9aab55c`

**Object language:** unchanged first-order HA over
\(\{0,S,+,\times,=\}\)

**Kernel change:** none

**Classical axioms:** none

This RFC freezes the first five B5 support rows. They connect prime divisors
and canonical valuations to the central coefficient and expose the three
live prime ranges after the two outer ranges have been eliminated. The words
**must**, **must not**, **should**, and **may** are normative.

## 1. Scope and non-claims

This tranche proves:

1. every prime divisor of `CentralBinom(n,c)` is at most `n+n`;
2. `NoBertrandClosed(n)` sharpens that bound to `p<=n`;
3. a nonzero canonical valuation exponent exposes its base as a divisor;
4. a prime divisor of a nonzero value forces a nonzero valuation exponent;
5. every central prime divisor under the no-Bertrand certificate lies in the
   small, middle, or row-bounded live range.

It discharges the outer prime-support requirement of B5 and makes the
five-range partition explicit at the divisor level. It does not yet bound a
complete prime-power contribution, prove the zero-contribution interval,
construct `central_binom_factorization_small`, or prove the final B5 upper
bound. It does not enroll a row or grant checked use.

## 2. Exact source seals

Stable arithmetic remains the only public authority. Candidate support must
be rebuilt from exact source bytes in dependency order. In particular, the
focused test must rebuild the checked Choose/factorial bridge, factorial
prime-divisor rows, power valuation stack, and Legendre valuation bridge.
Alpha membership and old receipts are never proof authority.

The new source is frozen at:

```text
peano-lab/py/peano_lab/library/
  bertrand_central_binom_prime_support_candidate.py
d48ed42c0b5289b1565947bb43dbcbe8389eed9aa196766ff90567cfc7fec7ab
```

The focused-test seal remains pending until all fail-closed receipts are
measured. Any source change invalidates the source seal and every receipt.

## 3. Exact public order, surfaces, and tags

The public row order is:

```text
central_binom_prime_divisor_le_double
no_bertrand_central_prime_divisor_le
power_valuation_nonzero_exponent_divides_base
prime_divisor_power_valuation_nonzero
no_bertrand_central_prime_divisor_ranges
```

All authoring abbreviations must be fully expanded before parsing. Define

```text
NoBertrandClosed(n)
  := forall r. (Lt(n,r) /\ Le(r,n+n)) -> ~Prime(r).
```

The exact abstract surfaces and public occurrence tags are:

```text
central_binom_prime_divisor_le_double
  forall n c p.
    Prime_bcpdl_prime(p) ->
    Central_bcpdl_central(n,c) ->
    Dvd_bcpdl_divides(p,c) ->
    Le_bcpdl_result(p,n+n)

no_bertrand_central_prime_divisor_le
  forall n c p.
    NoBertrandClosed_bnbcpdl_exclusion(n) ->
    Prime_bnbcpdl_prime(p) ->
    Central_bnbcpdl_central(n,c) ->
    Dvd_bnbcpdl_divides(p,c) ->
    Le_bnbcpdl_result(p,n)

power_valuation_nonzero_exponent_divides_base
  forall p c e.
    PowerVal_bpvnedb_source(p,c,e) ->
    ~(e=0) ->
    Dvd_bpvnedb_result(p,c)

prime_divisor_power_valuation_nonzero
  forall p c e.
    Prime_bpdvpn_prime(p) ->
    ~(c=0) ->
    PowerVal_bpdvpn_source(p,c,e) ->
    Dvd_bpdvpn_divides(p,c) ->
    ~(e=0)

no_bertrand_central_prime_divisor_ranges
  forall n s q c p.
    NoBertrandClosed_bnbcpdr_exclusion(n) ->
    Prime_bnbcpdr_prime(p) ->
    Central_bnbcpdr_central(n,c) ->
    Dvd_bnbcpdr_divides(p,c) ->
    (Le_bnbcpdr_small(p,s) \/
      ((Lt_bnbcpdr_above_small(s,p) /\
        Le_bnbcpdr_middle_bound(p,q)) \/
       (Lt_bnbcpdr_above_middle(q,p) /\
        Le_bnbcpdr_row_bound(p,n))))
```

The disjunction association and branch order shown above are binding.
`n+n` must retain the additive public spelling.

## 4. Exact direct dependencies

The direct dependency tuples, in first-use order, are:

```text
central_binom_prime_divisor_le_double
  factorial_exists
  choose_factorial_bridge
  mul_comm
  multiple_trans
  factorial_prime_le_of_divides

no_bertrand_central_prime_divisor_le
  le_total
  le_eq_or_lt
  le_refl
  central_binom_prime_divisor_le_double

power_valuation_nonzero_exponent_divides_base
  one_le_of_ne_zero
  power_valuation_power_divides
  power_divides_exponent_antitone
  pow_one

prime_divisor_power_valuation_nonzero
  pow_exists
  pow_one
  prime_power_divides_exponent_le_valuation
  le_zero

no_bertrand_central_prime_divisor_ranges
  le_total
  le_eq_or_lt
  le_refl
  no_bertrand_central_prime_divisor_le
```

The direct edge vector is `(5,4,4,4,4)`, totaling 21 live edges. No row may
use a dependency not listed here. Candidate-only support must be replayed
from its exact source factory and local prefix, never imported as authority.

## 5. Proof topology

### 5.1 Central prime-divisor upper bound

Choose factorial values for `(n+n)!` and `n!`. Apply
`choose_factorial_bridge` with the two identical column factorial witnesses,
so `(n+n)! = (n!*n!)*c`. Commute the outer factor to derive `c | (n+n)!`,
compose `p|c` by `multiple_trans`, and apply
`factorial_prime_le_of_divides`. No whole Central or Factorial rewrite is
allowed.

### 5.2 No-Bertrand sharpening

Split `p<=n` versus `n<=p` constructively. Equality closes by reflexivity.
The strict `n<p` branch combines the row-1 upper bound with the explicit
absence certificate and contradicts primality. The certificate is positive
negative-branch data; DNE is forbidden.

### 5.3 Valuation/divisor bridge

For the forward direction, project the selected prime power from the
valuation, lower its exponent to one, identify `p^1=p`, and retain the
divisibility witness. For the reverse direction, construct the exponent-one
power divisor from `p|c`, use the checked valuation dominance theorem, and
exclude exponent zero with `le_zero` and PA1. No host exponent calculation or
unique raw beta code may enter either proof.

### 5.4 Three live ranges

Obtain `p<=n` from row 2. Two isolated uses each of `le_total` and
`le_eq_or_lt` classify `p` first at `s` and then at `q`. Equality belongs to
the lower range in each split. The final branch carries both `q<p` and the
already checked `p<=n` bound.

## 6. Fail-closed evidence gates

The focused test must:

1. pin every executed candidate source and this RFC;
2. rebuild support from Stable plus exact dependency prefixes only;
3. exclude Alpha membership, registry mutation, and prior receipts;
4. independently rebuild all five public formulas and exact scripts;
5. freeze artifact, body, bounded envelope, and layered closure receipts;
6. reject all 21 dependency removals and `(statement) /\ false` targets;
7. reject one genuine semantic mutation for every row;
8. kernel-check, reject DNE, and enforce unchanged live resource caps before
   accepting any receipt; and
9. assert the direct root-dependency vector `(5,4,4,4,4)` and corrupt every
   root dependency edge before layered receipt acceptance.

Receipts are fail-closed: an absent value must fail, never skip. Expensive
roots must run one per fresh process. Parallel closure workers and cap raises
are forbidden.

## 7. Genuine mutations and counterfixtures

The required standard-model mutations are:

1. row 1 strengthens `Le(p,n+n)` to `Le(S p,n+n)`; use
   `(n,c,p)=(1,2,2)`;
2. row 2 weakens the absence certificate upper endpoint from `n+n` to `n`;
   use `(n,c,p)=(2,6,3)`;
3. row 3 changes the result divisor from `p` to `S p`; use
   `(p,c,e)=(2,2,1)`;
4. row 4 changes `~(e=0)` to `e=0`; use `(p,c,e)=(2,2,1)`;
5. row 5 weakens the absence certificate upper endpoint from `n+n` to `n`;
   use `(n,s,q,c,p)=(2,0,0,6,3)`.

The test must keep executable bounded semantic oracles for these fixtures.
Commuted multiplication, alpha-renamed binders, or disjunction reassociation
are not genuine mutations.

## 8. Capacity and release policy

The first two roots inherit the factorial bridge and factorial-divisor stack;
the valuation rows inherit the power-valuation stack. Layered replay must
root-prune and intern shared dependencies. No ordinary recursively duplicated
closure may justify a cap raise.

This tranche remains candidate-only. Its five rows may join the seven-row B4
capstone in a later 12-row additive Alpha microbatch after exact focused
evidence is complete. Stable and Alpha v10 remain byte-identical throughout
this tranche.
