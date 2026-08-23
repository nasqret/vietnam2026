# Constructive Kummer Theorem Campaign RFC v1

Status: complete constructive Kummer endpoint with dependency-curried body
evidence only; isolated candidate campaign with no Alpha enrollment, Stable
promotion, empty-context closure claim, or checked-use authority.

Date: 2026-08-23.

Parent edition: Alpha v12, containing 1,303 theorem specifications. Alpha
specifications used below are explicit premises of dependency-curried proof
bodies, not substitutes for empty-context certificates.

## 1. Mathematical endpoint

For every prime `p` and natural numbers `a,b`, construct a beta-coded sequence
of base-`p` addition carries and prove its bit count is exactly the valuation
of the relational binomial coefficient:

```text
Prime(p) -> Choose(a+b,a,C) -> PowerVal(p,C,e) ->
exists lb lc rb rc tb tc cb cc.
  PowerQuotientPrefix(p,a,lb,lc,a+b) /\
  PowerQuotientPrefix(p,b,rb,rc,a+b) /\
  PowerQuotientPrefix(p,a+b,tb,tc,a+b) /\
  AddQuotientCarryPrefix(lb,lc,rb,rc,tb,tc,cb,cc,a+b) /\
  BitCount(cb,cc,a+b,e).
```

Equivalently:

```text
v_p(C(a+b,a)) = number of carries when adding a and b in base p.
```

The length `a+b` is deliberately generous: all later power quotients vanish,
so the already-developed zero-tail infrastructure can align all three finite
quotient prefixes without requiring logarithms or a primitive digit function.
The isolated theorem `kummer_binomial_carry_bit_count` proves precisely this
endpoint as a dependency-curried intuitionistic body. Neither standalone
empty-context closure nor catalog admission has yet been performed.

## 2. Existing constructive infrastructure

The Bertrand campaign already supplies:

- relational `Choose`, factorial, `PowerVal`, and finite `LegendreSum`;
- the general complement-form identity
  `n! = (k! * j!) * Choose(n,k)` for `k+j=n`;
- exact prime-power valuation multiplicativity;
- Legendre's factorial-valuation identity;
- extended quotient prefixes, zero tails, beta-coded bits, and finite bit
  counts;
- a completed carry-count theorem only for the diagonal case `a=b=n`.

The important difference is that general Kummer requires **three** quotient
prefixes: one for `a`, one for `b`, and one for `a+b`. Bertrand's diagonal
proof only requires two because its two input prefixes coincide.

## 3. Implemented first tranche

Source:

```text
peano-lab/py/peano_lab/library/kummer_valuation_candidate.py
```

Focused audit:

```text
peano-lab/py/tests/test_kummer_valuation_candidate.py
```

Every readable relation is expanded to the unchanged first-order Peano kernel
language before parsing. The dependency order is:

1. `division_add_quotient_bit`:

   ```text
   DivRem(d,a,q,r) -> DivRem(d,b,s,t) -> DivRem(d,a+b,Q,R) ->
   (Q=q+s \/ Q=S(q+s)).
   ```

   No explicit nonzero-divisor assumption is needed: either `DivRem` premise
   already contains the strict remainder bound `r<d` or `t<d`. The proof
   splits constructively on `r+t<d`, `r+t=d`, or `d<r+t`, then invokes
   uniqueness of the canonical remainder.

2. `division_add_quotient_lower`:

   ```text
   DivRem(d,a,q,r) -> DivRem(d,b,s,t) -> DivRem(d,a+b,Q,R) ->
   q+s <= Q.
   ```

3. `division_add_quotient_upper`:

   ```text
   DivRem(d,a,q,r) -> DivRem(d,b,s,t) -> DivRem(d,a+b,Q,R) ->
   Q <= S(q+s).
   ```

4. `choose_factorial_valuation_balance`:

   ```text
   k+j=n -> Prime(p) -> Choose(n,k,C) -> PowerVal(p,C,e) ->
   FactorialVal(p,n,A) -> FactorialVal(p,k,B) ->
   FactorialVal(p,j,D) -> A=(B+D)+e.
   ```

   The proof obtains `k<=n` from its explicit complement witness `j`, uses
   constructive positivity of `Choose`, and applies exact valuation
   multiplicativity twice to the checked factorial identity. No subtraction
   primitive is introduced.

5. `choose_legendre_valuation_balance`:

   ```text
   k+j=n -> Prime(p) -> Choose(n,k,C) -> PowerVal(p,C,e) ->
   LegendreSum(p,n,A) -> LegendreSum(p,k,B) ->
   LegendreSum(p,j,D) -> A=(B+D)+e.
   ```

   This transports each of the three factorial valuations independently
   through the existing constructive Legendre theorem.

6. `binomial_legendre_valuation_balance`:

   ```text
   Prime(p) -> Choose(a+b,a,C) -> PowerVal(p,C,e) ->
   LegendreSum(p,a+b,A) -> LegendreSum(p,a,B) ->
   LegendreSum(p,b,D) -> A=(B+D)+e.
   ```

   This is the exact arithmetic valuation half of Kummer's theorem for
   arbitrary, possibly unequal inputs. Its identification with a coded carry
   count is provided by the separate second tranche below.

The six dependency-curried bodies have respectively 242, 46, 46, 169, 96,
and 66 proof nodes; all have depth at most 46. They contain no `DNE` and are
checked by the ordinary intuitionistic kernel. The 30 direct dependency edges
must all remain live.

## 4. Implemented three-prefix carry tranche and full Kummer endpoint

Source:

```text
peano-lab/py/peano_lab/library/kummer_carry_candidate.py
```

Focused audit:

```text
peano-lab/py/tests/test_kummer_carry_candidate.py
```

The capture-safe conservative relation is:

```text
AddCarryChoice(q,s,Q,bit) :=
  (bit=0 /\ Q=q+s) \/ (bit=1 /\ Q=S(q+s)).
```

The seven dependency-topological rows are:

1. `add_quotient_carry_choice`: functionality of powers and
   `division_add_quotient_bit` choose one bit for three arbitrary quotient
   prefixes at any shared index. Direct dependencies:

   ```text
   (pow_functional, division_add_quotient_bit)
   ```

2. `add_quotient_carry_prefix_extend`: beta-extends a stored carry code by
   one supplied terminal choice. Direct dependencies:

   ```text
   (beta_prefix_extend, finite_lt_succ_eq_or_lt)
   ```

3. `add_quotient_carry_prefix_exists`: natural-number induction constructs
   a complete beta-coded carry prefix for all three input prefixes. Direct
   dependencies:

   ```text
   (add_eq_zero_right, succ_ne_zero, le_succ, le_refl,
    add_quotient_carry_choice, add_quotient_carry_prefix_extend)
   ```

4. `add_quotient_carry_prefix_all_bits`: every decoded carry is zero or one.
   Direct dependencies: `()`.

5. `add_quotient_carry_prefix_restrict`: dropping a terminal position
   preserves the full three-prefix carry semantics. Direct dependencies:

   ```text
   (le_succ)
   ```

6. `beta_sum_add_carry_exact`: proves the exact three-prefix fold identity:

   ```text
   Sum(left,L) -> Sum(right,M) -> Sum(total,T) ->
   AddQuotientCarryPrefix(...) -> BitCount(bits,E) -> T=(L+M)+E.
   ```

   Direct dependencies:

   ```text
   (beta_sum_zero, beta_sum_succ_decompose, bit_count_zero,
    bit_count_succ_decompose, beta_at_unique, le_refl,
    add_quotient_carry_prefix_restrict, add_assoc, add_comm,
    add_shuffle_middle)
   ```

7. `kummer_binomial_carry_bit_count`: the complete arbitrary-input Kummer
   endpoint stated in Section 1. Existing zero-tail results extend the `a`
   and `b` prefixes to common length `a+b`; commutativity aligns the initially
   obtained right-prefix length `b+a`. The proof constructs all eight beta
   parameters, obtains a finite bit count, equates the valuation and carry
   balances, and cancels their shared Legendre sum. Direct dependencies:

   ```text
   (prime_legendre_sum_exists, binomial_legendre_valuation_balance,
    legendre_sum_extended_prefix_exists, add_comm,
    add_quotient_carry_prefix_exists,
    add_quotient_carry_prefix_all_bits, bit_count_exists,
    beta_sum_add_carry_exact, add_left_cancel)
   ```

The seven dependency-curried bodies have respectively 159, 131, 110, 42,
30, 640, and 268 proof nodes; their maximum depths are respectively 40, 44,
40, 24, 22, 78, and 65. They contain no `DNE`; all 30 direct dependency edges
are required. Together, the primary valuation and carry tranches comprise 13
kernel-checked candidate bodies and 60 mutation-tested live direct dependency
edges.

### 4.1. Constructive carry-free divisibility corollaries

The same isolated carry source exports a separate corollary factory containing
two additional dependency-curried proofs. Separating this factory preserves
the pinned primary endpoint and the bounded cost of its full edge-mutation
suite.

1. `prime_power_valuation_zero_iff_not_divides`:

   ```text
   Prime(p) -> ~(C=0) -> PowerVal(p,C,v) ->
   ((v=0 -> ~(p|C)) /\ (~(p|C) -> v=0)).
   ```

   The forward direction uses the existing theorem that a prime divisor of a
   nonzero value forces a nonzero valuation. The reverse direction performs a
   constructive equality decision on `v=0`; the nonzero branch would expose
   `p|C` and hence contradict the premise. Direct dependencies:

   ```text
   (prime_divisor_power_valuation_nonzero,
    power_valuation_nonzero_exponent_divides_base, eq_decidable)
   ```

2. `kummer_carry_free_iff_not_divides`:

   ```text
   Prime(p) -> Choose(a+b,a,C) -> PowerVal(p,C,v) ->
   exists lb lc rb rc tb tc cb cc.
     PowerQuotientPrefix(p,a,lb,lc,a+b) /\
     PowerQuotientPrefix(p,b,rb,rc,a+b) /\
     PowerQuotientPrefix(p,a+b,tb,tc,a+b) /\
     AddQuotientCarryPrefix(lb,lc,rb,rc,tb,tc,cb,cc,a+b) /\
     BitCount(cb,cc,a+b,v) /\
     ((BitCount(cb,cc,a+b,0) -> ~(p|C)) /\
      (~(p|C) -> BitCount(cb,cc,a+b,0))).
   ```

   Constructive positivity establishes that the coefficient is nonzero; the
   checked Kummer endpoint constructs the actual carry package; functionality
   of `BitCount` identifies a zero count with valuation zero. Direct
   dependencies:

   ```text
   (choose_positive, add_comm,
    prime_power_valuation_zero_iff_not_divides,
    kummer_binomial_carry_bit_count, bit_count_functional)
   ```

These two bodies have respectively 67 nodes/depth 27 and 194 nodes/depth 50.
They contain no `DNE`. Across all three factories the campaign now contains 15
constructively checked body proofs and 68 declared direct dependency edges;
the 60 primary-tranche edges additionally have exhaustive omission-mutation
tests.

The prime premise is essential. At composite base four,
`C(4,2)=6` has four-adic valuation zero, while the formal Legendre deficit is
`floor(4/4)-floor(2/4)-floor(2/4)=1`.

## 5. Remaining admission and proof-publication work

The full mathematical endpoint now has a checked constructive body, but the
following remain open and must not be conflated with that accomplishment:

1. Compile dependency-pruned empty-context `LayeredReplay` closures for the
   candidate DAG, keeping memory within the existing bounded replay contract.
2. Check layer-Cut integrity, independently pinned mutation/capacity gates,
   and source/provenance receipts for the entire transitive dependency graph.
3. If separately authorized, append a reviewed dependency-topological Alpha
   tranche without changing the sealed Stable release.
4. Promote to Stable only after its distinct closure and release gates pass.
5. Build a defined interactive proof explorer exposing `Choose`, `PowerVal`,
   `PowerQuotientPrefix`, `AddQuotientCarryPrefix`, `AllBits`, and `BitCount`
   as readable conservative definitions.

## 6. Resource and authority policy

The focused harnesses check independently replayed intuitionistic bodies,
exact direct dependencies, adversarial dependency removal, false targets,
3,750 independent prime-base numerical examples, explicit unequal-input carry
and no-carry/divisibility fixtures, capture-safe prefix binders, and the
composite-base counterexample. The largest body has 640 nodes and depth 78.
The current sealed Alpha-v12 and Stable catalogs remain unchanged.

These results are body evidence only. They are not standalone empty-context
proofs and do not authorize `replay`, checked use, an Alpha membership claim,
or a Stable release.
