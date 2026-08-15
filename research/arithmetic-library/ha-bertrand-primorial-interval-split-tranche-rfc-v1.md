# RFC HA-R6-BERTRAND-PRIMORIAL-3: interval products and prefix splitting

**Status:** binding subordinate statement, dependency, evidence, trust,
capacity, and release contract; no theorem is enrolled or admitted by this
document

**Parent campaign:**
[`RFC HA-R6-BERTRAND-1`](ha-bertrand-postulate-campaign-rfc-v1.md), SHA-256
`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`

**Representation amendment:**
[`RFC HA-R6-BERTRAND-2`](ha-bertrand-postulate-campaign-rfc-v2.md), SHA-256
`af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`

**Primorial foundation contract:**
[`RFC HA-R6-BERTRAND-PRIMORIAL-1`](ha-bertrand-primorial-foundation-tranche-rfc-v1.md),
SHA-256
`c68354c9aaad738581a14ccbe33e7eaa262940bad667d613e84b947454ff1a89`

**Primorial membership contract:**
[`RFC HA-R6-BERTRAND-PRIMORIAL-2`](ha-bertrand-primorial-membership-tranche-rfc-v1.md),
SHA-256
`4f569e76c68aa486fd1f1415491a5a3d678a75c239aa72ebd707d67fedde0df5`

**Immutable edition parent:** Alpha v9 at commit
`456f20b740791e304f34f8836c5b990954ee4694`

**Object language:** unchanged first-order HA over
\(\{0,S,+,\times,=\}\)

**Kernel change:** none

**Classical axioms:** none

This RFC freezes the eight-row B4 microbatch that introduces offset dense
selector products and splits `Primorial(a+l)` into a prefix and an interval
product. It reuses one pinned, kernel-replayed generic Product split theorem;
it does not authorize that provider's concat converse or any other candidate
Product theorem.

The words **must**, **must not**, **should**, and **may** are normative. The
campaign RFCs control the endpoint, logic, trust, and release policy. The two
earlier Primorial RFCs control `Sel`, `FactorPrefix`, and `Primorial`. This
document controls the eight new row names, order, surfaces, association,
occurrence tags, direct dependencies, proof topology, and evidence gates.

## 1. Scope and non-claims

This tranche supplies:

1. total and functional beta-coded selector prefixes for offset intervals;
2. total and functional `PrimorialInterval` values;
3. checked entry alignment between a dense global Primorial prefix and an
   independently coded interval prefix;
4. restriction of a prefix of length `a+l` to its first `a` entries; and
5. the exact factorization of `Primorial(a+l)` into its first `a` factors and
   the following `l` factors.

This is the representation bridge needed by the later filtered-product
comparison in B4. It does **not** prove duplicate-free prime-product
comparison, `primorial_le_four_pow`, any B5 five-range inequality, B7, B8,
BP01, or BP02.

This document creates no Alpha membership, checked-use grant, Stable
membership, publication, or deployment. All notation below is authoring
notation and must expand hygienically into ordinary first-order HA before
parsing.

## 2. Bound parent edition and provider bytes

The sole edition parent is the sealed Alpha-v9 snapshot at commit
`456f20b740791e304f34f8836c5b990954ee4694`:

- theorem count: `1076`;
- declared direct-edge count: `3276`;
- dependency-layer count: `45`;
- Stable count: `432`;
- Alpha-only count: `644`;
- checked-use count: `570`;
- evidence counts: `432 stable_closed`, `138 alpha_closed`,
  `505 body_checked`, and `1 pending_layered_closure`;
- ordered enrollment root:
  `fe862a0c9d0c47f05ae6740cbc95c67e9b984a715397e18078c11d44f709046f`;
- ordered specification root:
  `762d1310c41ed92da066701cf7529551324b09f7b501c5a29c530f443afeb998`;
- edition identity:
  `b74d7479d749500dbbd737f7cf5e7ea97a7998f8079233ed87b11c84823e2f80`;
- membership root:
  `4c87c40b5a260d67b5582447cfabb7e3ce62e80303aa4f4d33b1b952995ec356`;
- evidence root:
  `108593843459a69d81c333305a50b5368294c3c722437f425b92c942391fe9be`;
- channel-pointer root:
  `edfb0eacecbd9419b1b303098915e28e45643379b65ab7d807ffcd4d7bd4b3e7`;
- catalog SHA-256:
  `74ab887e9eef3e3fc583b103f392f4e06125cb14a561765373677eb57f830eda`;
- metrics SHA-256:
  `7397959a4dad4e1d42e6a108156c84666b4cd4f95e07e573d1fcf402f83c2d65`;
- dependency-graph SHA-256:
  `03b803080cd082642adeb2a89b62ab369c7e69aca4c4dfe90b327ef94c389ab9`;
  and
- channels SHA-256:
  `77fd0ba0ad1ba461432384c3330041a3dfc641dc84121982eb08456ee2de9a34`.

The Primorial foundation source is pinned at:

```text
peano-lab/py/peano_lab/library/bertrand_primorial_foundation_candidate.py
70e50275253977d96537a256c2b0b676975ade8464c33b29786b5f70963e7a98
```

The generic split provider is pinned at:

```text
peano-lab/py/peano_lab/library/finite_product_prefix_suffix_candidate.py
b0e98632b5668a688067ecdddebe0f906db00ebe84c267b395592d5797d27d9d

peano-lab/py/tests/test_finite_product_prefix_suffix_candidate.py
86697086ff795fc1b3947e0470eba300f1c6e416e6f23b1c18dc2d5179ae5738
```

Only `beta_product_prefix_suffix_split`, the first row of that provider, is
permitted. `beta_product_prefix_suffix_concat` is forbidden as authority.
The permitted split row must be rebuilt and closed recursively from its
source and Stable dependencies. Its prior candidate receipt is not authority.

The new candidate source is frozen at:

```text
peano-lab/py/peano_lab/library/bertrand_primorial_interval_candidate.py
02e59e0f7addcae3bb127271ddeaa6728c5dab1dee096a878fced278065c10a3
```

The focused-test byte seal remains pending until the fail-closed receipts are
measured. If source debugging changes the source hash, this RFC and every
source pin must be updated together before release.

No implementation may edit any Alpha-v1 through Alpha-v9 or Stable ledger,
artifact, root, pointer, canonical position, origin, or evidence record.
Alpha membership and `body_checked` evidence are not theorem authority.

## 3. Exact representation

The inherited definitions are:

```text
Sel(i,p) :=
  (Prime(S i) /\ p = S i) \/
  (~Prime(S i) /\ p = 1)

FactorPrefix(b,c,m) :=
  forall i. Lt(i,m) ->
    exists p. BetaAt(b,c,i,p) /\ Sel(i,p)

Primorial(m,z) :=
  exists b c. FactorPrefix(b,c,m) /\ Product(b,c,m,z)
```

The new offset representation is exactly:

```text
IntervalPrefix(a,b,c,l) :=
  forall i. Lt(i,l) ->
    exists p. BetaAt(b,c,i,p) /\ Sel(a+i,p)

PrimorialInterval(a,l,z) :=
  exists b c.
    IntervalPrefix(a,b,c,l) /\ Product(b,c,l,z)
```

Thus `PrimorialInterval(a,l,z)` covers candidates `a+1` through `a+l`.
The public carrier is additive `a + l`; it must not be silently normalized
to another representation. Private builders must parse terms in an explicit
context, pretty-print the AST, and generate collision-free binders.

## 4. Frozen occurrence tags

| Row | Public occurrence tags |
|---|---|
| `primorial_interval_factor_prefix_extend` | `bpifpe_before`, |
| | `bpifpe_after` |
| `primorial_interval_factor_prefix_exists` | `bpifpx_result` |
| `primorial_interval_factor_prefix_transport_entry` | `bpifpt_left`, |
| | `bpifpt_right` |
| `primorial_interval_exists` | `bpi_exists` |
| `primorial_interval_functional` | `bpi_functional_left`, |
| | `bpi_functional_right` |
| `primorial_interval_factor_prefix_shift` | `bpifps_source`, |
| | `bpifps_interval` |
| `primorial_factor_prefix_restrict_add` | `bpfpra_source`, |
| | `bpfpra_target` |
| `primorial_prefix_interval_split` | `bppis_source`, |
| | `bppis_prefix`, `bppis_interval` |

Private proof tags may extend these stems but must remain collision-safe.
Changing any public tag, binder order, association, or helper expansion
requires a versioned successor contract.

## 5. Exact theorem order, surfaces, and direct dependencies

The order below is immutable and every dependency tuple is ordered.

1. `primorial_interval_factor_prefix_extend`

   ```text
   forall a b c l.
     IntervalPrefix(a,b,c,l) ->
     exists d e. IntervalPrefix(a,d,e,S l)
   ```

   Dependencies: `primorial_factor_choice_exists`, `beta_prefix_extend`,
   `finite_lt_succ_eq_or_lt`.

2. `primorial_interval_factor_prefix_exists`

   ```text
   forall a l. exists b c. IntervalPrefix(a,b,c,l)
   ```

   Dependencies: `add_eq_zero_right`, `succ_ne_zero`,
   `primorial_interval_factor_prefix_extend`.

3. `primorial_interval_factor_prefix_transport_entry`

   ```text
   forall a b c d e l.
     IntervalPrefix(a,b,c,l) -> IntervalPrefix(a,d,e,l) ->
     forall i p. Lt(i,l) -> BetaAt(b,c,i,p) -> BetaAt(d,e,i,p)
   ```

   Dependencies: `beta_at_unique`,
   `primorial_factor_choice_functional`.

4. `primorial_interval_exists`

   ```text
   forall a l. exists z. PrimorialInterval(a,l,z)
   ```

   Dependencies: `beta_product_exists`,
   `primorial_interval_factor_prefix_exists`.

5. `primorial_interval_functional`

   ```text
   forall a l x y.
     PrimorialInterval(a,l,x) -> PrimorialInterval(a,l,y) -> x = y
   ```

   Dependencies: `beta_product_transport_prefix`,
   `beta_product_functional`,
   `primorial_interval_factor_prefix_transport_entry`.

6. `primorial_interval_factor_prefix_shift`

   ```text
   forall a b c d e l.
     FactorPrefix(b,c,a+l) -> IntervalPrefix(a,d,e,l) ->
     forall i p.
       Lt(i,l) -> BetaAt(b,c,a+i,p) -> BetaAt(d,e,i,p)
   ```

   Dependencies: `add_le_add_left`, `beta_at_unique`,
   `primorial_factor_choice_functional`.

7. `primorial_factor_prefix_restrict_add`

   ```text
   forall a b c l.
     FactorPrefix(b,c,a+l) -> FactorPrefix(b,c,a)
   ```

   Dependencies: `le_add_right`, `lt_of_lt_of_le`.

8. `primorial_prefix_interval_split`

   ```text
   forall a l z.
     Primorial(a+l,z) ->
     exists x y.
       Primorial(a,x) /\
       (PrimorialInterval(a,l,y) /\ z = x * y)
   ```

   Dependencies: `beta_product_prefix_suffix_split`,
   `primorial_interval_factor_prefix_exists`,
   `primorial_interval_factor_prefix_shift`,
   `primorial_factor_prefix_restrict_add`.

The exact direct-edge count is `22`. The exact direct-`Cut` vector is:

```text
(3, 3, 2, 2, 3, 3, 2, 4)
```

Removing any edge independently must make its focused replay fail.

## 6. Required proof topology

1. Row 1 selects the global candidate `a+l`, calls the stable beta-prefix
   extension once, and splits `Lt(i,S l)` into `i=l` or `i<l`. The terminal
   branch rewrites only the resulting small formulas; the earlier branch
   reuses the supplied interval prefix.
2. Row 2 inducts on `l`. Its zero branch is vacuous by the strict-bound
   witness and successor nonzero; its step applies row 1 to the generalized
   induction hypothesis.
3. Row 3 extracts one selector witness from each prefix, uses
   `beta_at_unique` and selector functionality, and transports only the
   decoded value. It must rewrite both occurrences of that value in the
   expanded target `BetaAt`.
4. Row 4 obtains a prefix and a Product value through separate theorem
   applications, cases each inference-produced existential, and packages the
   relational interval.
5. Row 5 constructs the pointwise Product transport premise by applying row
   3 through its prefix parameters, transports the left Product, and invokes
   Product functionality. No beta-code equality is asserted.
6. Row 6 derives `Lt(a+i,a+l)` from `Lt(i,l)` with `add_le_add_left` and one
   isolated successor-addition equality, obtains both selector witnesses,
   and aligns the decoded values exactly as in row 3.
7. Row 7 obtains `Le(a,a+l)` from `le_add_right` and composes it with each
   strict source bound using `lt_of_lt_of_le`.
8. Row 8 unpacks the source Primorial, constructs an independent interval
   prefix, proves the shift premise with row 6, invokes the pinned Product
   split once, and packages the restricted prefix Product and interval
   Product without identifying their beta codes.

Every existential later eliminated must come directly from an inferable
theorem or hypothesis application. DNE, classical choice, raw code equality,
whole-relation rewrites, `beta_product_prefix_suffix_concat`, and all
candidate-only Product order rows are forbidden.

## 7. Focused evidence and authority boundary

The implementation must have one focused fail-closed test. It must rebuild
all eight public and proof-local formulas independently and compare exact
names, order, statements, tags, scripts, and dependency tuples.

For each row, authority is exactly:

1. Stable checked-use theorems;
2. the recursively rebuilt pinned ten-row Primorial foundation;
3. the recursively rebuilt first row only of the pinned Product split
   provider; and
4. the earlier local prefix of this tranche.

Alpha-v9 membership, body receipts, closure receipts, later local siblings,
the split provider's concat row, arbitrary provider scans, and every B5/B7/
B8/BP01/BP02 theorem are not authority.

Each row needs concrete artifact, body, bounded-envelope, and independently
kernel-accepted empty-context closure receipts. A missing value or receipt
comparison before the semantic gates is fail-closed.

## 8. Liveness, mutations, and closure gates

All `22` edges must be live. Every target must reject conjunction with
`false`. At least one genuine counterfixture-backed mutation is required per
row. The minimum set is:

1. replace row 1's existentially fresh successor prefix by the unchanged
   source code; refute it at offset `1`, length `0`, and source code `0`;
2. require the row 2 code witness to equal `0`; refute it at offset `1`,
   length `1`;
3. shift row 3's target decoded value from `p` to `S p` at the selected
   factor `2`;
4. require row 4's interval result to equal `0` at offset `1`, length `1`;
5. strengthen row 5's conclusion to `x = S y` at length `0`;
6. shift row 6's target decoded value from `p` to `S p` at offset `1`,
   length `1`;
7. strengthen row 7's target length from `a` to `S a` at `a=l=0` with a
   vacuous source code; and
8. strengthen row 8's product equation to `z = S (x*y)` at `a=l=0`.

Equivalent alpha-renamings, commuted products, or other true statements do
not count. Every mutation must replace a unique expanded substring.

Each empty-context closure must pass the intuitionistic kernel, bounded
envelope, current resource caps, and zero-DNE gate. It must then have the
exact direct-`Cut` count from Section 5. Every direct Cut must be corrupted
and kernel-rejected before the closure receipt is accepted.

## 9. Capacity and release policy

The unchanged campaign limits are:

- `4096` candidate body proof nodes;
- `65536` candidate body edges;
- `500000` empty-context proof occurrences;
- `100000` distinct empty-context proof objects;
- proof and envelope depth `256`; and
- `5000000` annotation occurrences.

The generic Product split and row 8 are the principal closure risks. Receipts
must be measured serially in fresh processes; limits may not be raised.

After all evidence passes and an independent audit is clean, this tranche
may be proposed for an additive Alpha successor. Initial enrollment must be:

```text
membership = alpha_only
evidence = body_checked
checked_use = false
proof_tag = null
empty_context_closure = null
```

Stable remains unchanged. Focused closure evidence does not itself grant
checked use, `alpha_closed`, or Stable membership.

## 10. Acceptance checklist

- [ ] all parent roots, RFC hashes, provider hashes, and the source hash
      reproduce exactly;
- [ ] all eight surfaces, scripts, tags, descriptions, and ordered dependency
      tuples reproduce exactly;
- [ ] all `22` edge removals, eight false targets, eight genuine mutations,
      and helper hygiene checks fail closed;
- [ ] all bodies, envelopes, and closures pass kernel, cap, and no-DNE gates;
- [ ] direct Cuts are exactly `(3, 3, 2, 2, 3, 3, 2, 4)` and every Cut
      corruption is rejected before receipt comparison;
- [ ] only `beta_product_prefix_suffix_split` is admitted from the pinned
      candidate provider;
- [ ] there is no Alpha/Stable/provider authority leakage; and
- [ ] Alpha-v1 through Alpha-v9 and Stable remain byte-identical.

Passing this checklist establishes only the eight-row candidate tranche. It
does not complete B4 or Bertrand's postulate.
