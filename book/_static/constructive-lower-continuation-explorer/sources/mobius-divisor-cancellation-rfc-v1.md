# Constructive Möbius divisor-sum cancellation

This additive checkpoint proves the complete positive-input identity

```text
sum_{d | n, d > 0} mu(d) = 1  if n=1,
                         0  if n>1.
```

The values, finite tables, divisor masks, quotient witnesses, permutations
and signed sum traces are all the existing genuine arithmetic graphs.
The canonical signed code of `+1` is **2**, not 1. This is the cancellation
prerequisite of G007, **not** the full Möbius-inversion theorem: the general
divisor-convolution/Fubini composition and inversion for arbitrary finite
arithmetic functions remain separate obligations.

## Exact authority boundary

The unchanged parent is Alpha v30, with 3,222 checked-use theorems and
Stable432. Its catalogue SHA-256 is
`ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7`.
The earlier 170 and 126 research-checkpoint rows remain non-admitted.
The new sources neither change their definitions nor confer Alpha or Stable
membership. No kernel, trusted checker, resource gate, old artifact,
publisher, or global definition registry is modified.

This RFC records actual original-HA **conditional-body** replay. Complete
dependency-closed artifacts, independently compiled Lean acceptance, and
ordinary empty-context principal certificates must be checked by the
integration layer before those stronger labels are claimed. Source hashes,
stored metrics and finite numerical examples are never proof authority.

## Construction, without an assumed cancellation law

1. For an actual prime `p`, toggle a positive integer `d` by adding `p`
   when `p` does not divide `d`, removing it when its exponent is exactly
   one, and fixing `d` when `p*p` divides it. The removal branch contains
   the actual equation `d=p*e` and proves that `p` does not divide `e`.
2. If `p | n`, Euclid cancellation proves that this toggle preserves the
   positive divisors of `n`. Extend by identity at zero and nondivisors.
3. Ordinary finite induction and the unchanged beta-prefix constructor
   produce a real map on **S n entries**, the interval `0,...,n`.
   The proved symmetric and functional graph gives injectivity; actual
   divisor bounds and constructive finite surjectivity give a permutation.
4. The independently defined Möbius value changes sign along the toggle.
   The prime-square fixed cases are proved to have value zero. Zero and
   nondivisors contribute zero because of the existing divisor mask,
   independently of the source table's entry at zero.
5. Construct the actual signed pullback table. The old finite-sum
   permutation theorem preserves its sum, while a new checked
   pointwise-negation theorem negates the sum. The old proved fact that a
   canonical signed integer equal to its negative is zero finishes
   cancellation. At `n=1`, the actual two-entry mask fold is `0+mu(1)=+1`.

The proof uses no choice axiom, classical principle, factor-list oracle,
assumed permutation, supplied quotient bound, or supplied divisor-sum
identity. It does not need the separate new rectangular-Fubini campaign.

## Reusable conservative relations

`PrimeFactorToggle(p,d,e)` is exactly the disjunction

```text
(not Divides(p,d) /\ e=p*d)
\/
(d=p*e /\ not Divides(p,e))
\/
(Divides(p*p,d) /\ e=d).
```

`DivisorPrimeToggle(n,p,d,e)` applies that graph when `d != 0` and `d | n`;
otherwise its explicit `d=0 or not Divides(d,n)` branch requires `e=d`.
`DivisorPrimeTogglePrefix(n,p,b,c,l)` records an actual beta entry and that
graph for every `i<l`. A relation alone does not assert that `p` is prime,
divides `n`, or preserves a bounded interval; the theorem premises and
proofs supply those obligations explicitly.

`ArithTableNegation(F,G,l)` says that any actual canonical signed lookups
of `F` and `G` at each `i<l` satisfy the unchanged `SignedNegate` graph.
It contains no sum identity and no implicit table-validity assertion.

`MobiusPositiveTableValues(N,F)` says only

```text
forall d z. d != 0 -> d <= N -> ArithAt(F,d,z) -> Mobius(d,z).
```

It is the positive-value clause already present inside `MobiusTable`,
separately named without changing that frozen definition. It does not
restrict `F(0)`. The unrestricted-zero-entry principal theorem explicitly
also requires the existing real `ArithTable(N,F)` graph, so malformed
table codes do not satisfy the premise vacuously.

The public builders, all with keyword-only `tag` and `variables`, are:

```python
prime_factor_toggle_relation(p, d, e, *, tag, variables)
divisor_prime_toggle_relation(n, p, d, e, *, tag, variables)
divisor_prime_toggle_prefix_relation(n, p, b, c, l, *, tag, variables)
signed_arithmetic_table_negation_relation(F, G, l, *, tag, variables)
mobius_positive_table_values_relation(N, F, *, tag, variables)
```

All accept compound terms and reject collisions of every generated binder
with the whole explicit context. Existing divisibility, primality, beta,
Möbius, signed lookup, negation, table, mask, permutation and sum definitions
are reused. This RFC assigns no global definition IDs.

## Three principal cancellation endpoints

1. `mobius_divisor_sum_cancellation`:

   ```text
   forall N M n z.
     MobiusTable(N,M) -> n != 0 -> n <= N ->
     (DivisorSum(M,n,z) <->
       ((n=1 /\ z=2) \/ (n!=1 /\ z=0))).
   ```

   Both implications are proved. The existing `DivisorSum` is still the
   genuine zero-masked S n-entry fold, never defined by this result.
2. `mobius_divisor_sum_cancellation_exists` constructs `M,z` for each
   positive `n`, proving `MobiusTable(n,M)`, the actual `DivisorSum(M,n,z)`,
   and the precise unit/nonunit result. No table is supplied as an oracle.
3. `mobius_divisor_sum_cancellation_on_positive_values` replaces
   `MobiusTable(N,M)` by `ArithTable(N,F)` and
   `MobiusPositiveTableValues(N,F)`. It proves the same exact equivalence
   for `DivisorSum(F,n,z)` with **F(0) entirely unrestricted**.

The finite prime-toggle construction is also exposed as
`divisor_prime_toggle_permutation_exists`, requiring `n != 0`, actual
`Prime(p)` and `Divides(p,n)`, and returning both the genuine prefix graph
and the unchanged full bounded/injective/surjective permutation relation.

## Frozen mathematical inventory

Factory: `make_mobius_divisor_cancellation_candidate_theorems(TheoremSpec)`
in `peano-lab/py/peano_lab/library/mobius_divisor_cancellation_candidate.py`.

```text
prime_toggle_square_quotient_divides
prime_toggle_fresh_divisor_product
prime_factor_toggle_exists
prime_factor_toggle_functional
prime_factor_toggle_symmetric
prime_factor_toggle_positive
prime_factor_toggle_preserves_divisor
divisor_prime_toggle_exists
divisor_prime_toggle_functional
divisor_prime_toggle_symmetric
divisor_prime_toggle_bounded
divisor_prime_toggle_prefix_exists
divisor_prime_toggle_prefix_lookup
divisor_prime_toggle_prefix_permutation
divisor_prime_toggle_permutation_exists
mobius_prime_factor_toggle_negates
mobius_divisor_mask_actual_value
mobius_divisor_mask_prime_toggle_negates
signed_table_swapped_components_negation_at
signed_prefix_sum_pointwise_negate
anti_invariant_signed_permutation_sum_zero
mobius_divisor_mask_prime_factor_sum_zero
mobius_divisor_sum_nonunit_value_zero
mobius_divisor_sum_nonunit_zero
mobius_divisor_sum_unit_one
mobius_divisor_sum_cancellation
mobius_divisor_sum_cancellation_exists
mobius_divisor_sum_cancellation_on_positive_values
```

There are **28 rows**, **99 declared edges**, and **1,569 tactic commands**.
All dependencies are used and topological. Exact AST novelty includes all
3,518 earlier rows and the separate twelve new divisor-involution rows.
The ordered-names SHA-256 (newline-joined with final newline) is
`ae5eb369778d001f572fa340f7c5aba2a9c573ffcd78061ff12d01a389cc4aab`.

Only untrusted tactic-generating Python helpers are imported from the new
divisor-involution module. **No one of its twelve theorem rows is a proof
dependency of this factory.** Source-code reuse must not be rendered as
an invented mathematical prerequisite arrow, nor counted again as a new
cancellation theorem.

| Source | SHA-256 |
|---|---|
| `peano-lab/py/peano_lab/library/mobius_divisor_cancellation_candidate.py` | `9af47fd019e5899586cb02c0e124579d82c4b65d093cfc73d721f411130b457f` |
| `peano-lab/py/tests/test_mobius_divisor_cancellation_candidate.py` | `c54f1b00dd3e60d4b0ee389a6f8626dccaf964bf94271b984f465e639a3f783e` |

| Principal statement | Literal statement SHA-256 |
|---|---|
| `mobius_divisor_sum_cancellation` | `dc605f677a0cdb931e7f3e65b29569dea83f1b9db136b932913a1936dc2b3406` |
| `mobius_divisor_sum_cancellation_exists` | `50bcf039c53ca70483eadd8ff3f9c3baf484d1fc82f84afe21009620ff674280` |
| `mobius_divisor_sum_cancellation_on_positive_values` | `be20bbedecba3566c7d3611f121e3d2e4fdaffd7fdee715dcd7e60afdb4cfd56` |
| `divisor_prime_toggle_permutation_exists` | `76ed082f3e75e22e2a1f0bbb45321b76ef34d24837573006f7b20061b972acf7` |

## Validation

All 28 original conditional bodies have been accepted with unchanged
authoring limits. They contain **3,271 summed proof occurrences** and
**3,238 summed per-body distinct objects** (not a claim of globally distinct
shared objects). The largest body has **322** occurrences; maximum depth
is **59**. Exact per-row occurrence/object/depth metrics are pinned in tests.

The complete final focused suite passed **169/169 tests**, with no skipped
cases, in **143.34 seconds** (143.511484 seconds including runner overhead),
at an observed peak RSS of **403,603,456 bytes**. All original body checks,
exact contracts, hostile inputs and numerical witness checks ran in that
fresh bounded process. The mathematical source remained unchanged through
the final independent-contract and full-suite reruns.

The tests include independent exact principal and relation ASTs; every
nested binder against the entire context; compound terms and large binary
numerals; exact novelty; false conclusions, absent dependencies and
altered domain/output contracts; real CRT-built prime-toggle maps; actual
paired-beta signed tables and prefix-sum traces; prime-square fixed points;
nondivisor identity; the unit, excluded-zero and finite-domain boundaries;
and negative, zero and positive unrestricted input values at index zero.

With `PYTHONPATH=peano-lab/py`, the dedicated test-file CLI checks all bodies
under CPU limits170/175 seconds, a180-second wall alarm and an observed
RSS ceiling of1,536MiB. The same limits are used around the full pytest
suite. No original mathematical or execution limit has been increased.

```sh
python3 peano-lab/py/tests/test_mobius_divisor_cancellation_candidate.py
python3 -m pytest -q peano-lab/py/tests/test_mobius_divisor_cancellation_candidate.py
```
