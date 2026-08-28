# G014: Euler's theorem for actual modular units

Date: 2026-08-28.

This is an additive, local proof development over the immutable Alpha-v30
parent: 3,222 checked theorems and unchanged Stable 432. The exact authoring
catalogue is `artifacts/peano-library/alpha/catalog-v30.json`, SHA-256
`ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7`.
No existing proof source, kernel, tactic engine, resource limit, admission,
catalogue, definition registry, worker, or public snapshot is modified.

## Exact result and domain

The principal theorem `euler_theorem_for_units` matches G014 literally:

```text
∀ a m t.
  (1<m ∧ (Unit(a,m) ∧ Phi(m,t))) →
  ∃ w. Pow(a,t,w) ∧ ModEq(m,w,1).
```

Here `Unit(a,m)` is exactly

```text
1<m ∧ ∃ b. b<m ∧ ModEq(m,a*b,1).
```

It is not the older `UnitResidue(m,a)` range predicate, which says only that
`a` is nonzero and below the modulus. `euler_modular_unit_coprime` and
`euler_coprime_modular_unit` prove the equivalence with the established
common-divisor `Coprime(a,m)` relation on the domain `m>1`.

The stronger theorem `euler_coprime_totient_power` proves

```text
∀ a m t. m≠0 → Coprime(a,m) → Phi(m,t) →
  ∃ w. Pow(a,t,w) ∧ ModEq(m,w,1).
```

The companion `euler_coprime_totient_power_value` proves the congruence for
every supplied actual `Pow(a,t,w)` value. The existence theorem constructs
that power; it does not require one as a premise. Neither theorem requires
`a<m`, primality, a factorization, a reduced-residue enumeration, a supplied
permutation, or an assumed finite-product identity.

`Phi` is the **unchanged independently defined G006 graph**: positive modulus
and the sum of actual coprimality-indicator bits on **`0≤i<m`**. No Euler
congruence or product formula is inserted into its definition. `Pow`,
`Product`, `BetaAt`, `Coprime`, strict order, and balanced `ModEq` also retain
their established primitive HA meanings.

The broader coprime theorem genuinely includes `m=1`: `Phi(1,1)` counts the
sole canonical residue zero. Its conclusion is congruence to one, **not** the
false claim that one is a bounded canonical remainder modulo one. At that
boundary the weighted product below is zero, and `Coprime(0,1)` is true; the
existing modular cancellation theorem remains applicable. `Phi(0,t)` remains
excluded by its frozen definition and theorem. G014 itself retains `m>1`.

## Conservative definitions and exact builder interfaces

The following five builders are new. They do not allocate registry IDs.
Each accepts keyword-only `tag` and optional `variables`.

| Public builder | Positional arguments | Independent graph |
| --- | --- | --- |
| `modular_unit_relation` | `a,m` | `m>1` and a genuinely witnessed inverse `b<m`. |
| `unit_multiplier_prefix_relation` | `a,m,b,c,l` | For every `i<l`, an actual `BetaAt(b,c,i,r)` with `r<m` and `a*i≡r (mod m)`. |
| `unit_product_factor_relation` | `m,i,v` | `Coprime(i,m) ∧ v=i`, or `¬Coprime(i,m) ∧ v=1`. |
| `unit_product_prefix_relation` | `m,b,c,l` | At every `i<l`, an actual decoded factor with the preceding choice graph. |
| `unit_scaled_prefix_relation` | `a,m,b,c,d,e,l` | At each actual pair of source/target entries below `l`, unit indices satisfy `a*source≡target`; nonunit indices satisfy `source≡target`. |

The first two are in `euler_units_residue_candidate.py`; the remaining three
are in `euler_units_product_candidate.py`. The explicit context is a
nonempty tuple of distinct valid variable names. Arguments are parsed as
actual HA terms in that context, so compound terms and large numerals are
supported. The complete expansion is reparsed, and **all generated binders
are checked against the entire declared context, including unused names**.
For backwards-compatible identifier-only calls, omitting `variables` infers
the distinct identifier arguments. Compound arguments require the explicit
context.

The independent AST tests compare all five graphs to separately written
primitive definitions, verify alpha-renaming, test compound/large terms,
and reject every generated binder as an unused hostile context name. There
is no new parser or kernel constant.

The mathematical definition dependencies are acyclic:

```text
Lt + ModEq ────────────────────────────────> Unit
Lt + BetaAt + ModEq ───────────────────────> UnitMultiplierPrefix
Coprime ──> UnitProductFactor
Lt + BetaAt + UnitProductFactor ───────────> UnitProductPrefix
Lt + BetaAt + Coprime + ModEq ─────────────> UnitScaledPrefix
```

None of these graphs mentions `Phi`, `Pow`, or the final Euler conclusion.
The connection between the independently counted bits and the product's
exponent is a theorem, not a definition edge or an assumed count oracle.

## Constructive proof route

1. Frozen gcd periodicity proves that balanced congruence transports actual
   coprimality, even before requiring a positive modulus. Multiplication by
   a coprime `a` preserves and reflects the unit predicate at corresponding
   residue indices.
2. Actual Euclidean division constructs the residue of `a*i` at each index.
   HA induction and `beta_prefix_extend` construct the entire multiplier
   code. Coprime modular cancellation proves injectivity; the existing
   constructive finite pigeonhole theorem supplies surjectivity.
   `euler_multiplier_permutation_exists` exposes the actual code together
   with its boundedness, injectivity, and surjectivity.
3. Independently decide `Coprime(i,m)` and construct the beta-coded factor
   `F(i)=i` for units, `F(i)=1` otherwise. Ordinary finite-product induction
   proves `euler_unit_product_coprime`: the actual product is coprime to `m`.
4. Frozen `finite_beta_composition_exists` constructs the reindexed factor
   list along the actual multiplier code. Existing exact finite-product
   permutation invariance proves the two complete products equal. The new
   `euler_unit_product_reindex_scale` proves that this actual composition
   scales precisely the unit positions.
5. A separate arbitrary-prefix induction proves
   `euler_unit_count_product_balance`. Decompose the real unit count into its
   predecessor and independently chosen zero/one bit, and decompose both
   actual product traces. A one bit uses the actual successor-power law;
   a zero bit leaves the exponent unchanged. Thus, for arbitrary length,
   `UnitCount(m,l,t)`, actual unit-scaled prefixes, both actual product values
   `P,Q`, and actual `Pow(a,t,w)` imply `w*P≡Q (mod m)`.
6. Apply that theorem to length `m`. Exact reindexing gives `Q=P`, and the
   proved coprimality of `P` permits G013 cancellation. Finally `pow_exists`
   supplies the actual exponentiation witness and the bounded-inverse unit
   bridge yields the exact G014 statement.

This proof uses neither prime-power Euler statements nor a binomial or
group-order assumption. It proves no multiplicative-order minimality,
Lagrange theorem, G015, or RSA endpoint.

## Exact duplicate removal and preserved history

The current candidate has **32 distinct new theorems**, not 34. An exact
parsed-formula audit found two scalar claims already proved in the immutable
parent. Their candidate aliases have been removed, and their consumers now
directly name the existing proofs:

| Removed candidate alias | Reused parent theorem |
| --- | --- |
| `euler_modulus_above_one_nonzero` | `binary_modulus_nontrivial_nonzero` |
| `euler_product_scale_shuffle` | `mul_shuffle_four` |

This is a reuse of identical quantified HA statements, not a weakening of
either claim. The other 32 statement strings and all five definition builders
are unchanged. The weighted-product module is byte-identical. Tests pin the
complete ordered surviving statements, check the two reused parent formulas
independently, and reject corruption of each directly reused dependency.

The valid 34-row v1 proof checkpoint is retained as **superseded, non-admitting
proof data**, together with its original mathematical sources and RFC in
`research/arithmetic-library/artifacts/bottom-layer-euler-units-v1-sources/`.
It is not overwritten or counted as 34 new facts. The current deduplicated
checkpoint uses the separate `bottom-layer-euler-units-proof-bundle-v2.json`
artifact. Neither checkpoint changes Alpha or Stable membership.

## Inventory, integration order, and exact pins

The factories are topologically ordered as follows:

| Module | Factory | Rows | Direct dependencies | Commands | Body nodes | Maximum depth |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `euler_units_residue_candidate.py` | `make_euler_units_residue_candidate_theorems` | 12 | 29 | 376 | 549 | 36 |
| `euler_units_product_candidate.py` | `make_euler_units_product_candidate_theorems` | 14 | 29 | 430 | 715 | 39 |
| `euler_units_candidate.py` | `make_euler_units_candidate_theorems` | 6 | 33 | 397 | 665 | 61 |
| Total | | 32 | 91 | 1,203 | 1,929 | 61 |

There are 1,925 body proof objects, with four reused objects in the count
induction. Its 379 nodes are the largest single body. Ordered-name SHA-256,
joining all 32 names with newline and **no trailing newline**:
`cd20126240c0f26016e1e6952a491db20eaf6759ecb4b795908db05635d30bd3`.

The complete ordered frontier-specification digest, including every name,
statement, ordered dependency, script, and summary, is
`38ecc1c3c4a6045b7fb301526b09ede9b7927524265909bd59bdbbef1dfaf02e`.
The compact JSON digest of the ordered `(name, statement)` pairs is
`7b3957933ea7a0f6d0c6651734a94b70f8a9d4b8f082de0cc18dd6c47560363a`,
exactly matching the original statements with only the two aliases omitted.

Current mathematical source SHA-256 pins:

| Source | SHA-256 |
| --- | --- |
| `euler_units_residue_candidate.py` | `dacb55219a5a5e9856d208a73e39b77156977d1de7d882044d4ed52907a7fdee` |
| `euler_units_product_candidate.py` | `dfbbc7dd69672992eb99a4eb99f64fb8273c28838aa6e1e749eb5b8a075ef8b9` |
| `euler_units_candidate.py` | `46e69f301a7215929958726a12ee151ad1972b771bcee57250a8fbbf18873458` |

Principal statement SHA-256 pins:

| Theorem | SHA-256 |
| --- | --- |
| `euler_multiplier_permutation_exists` | `ee049e3a4d625ec0da3ab6d4ecff22da14d26fb3d4297031b23b2ece92c14fec` |
| `euler_unit_product_coprime` | `d916c0ca5702f2b839e086c3921bc113ea614f0eb2564ab86f034bc8c1ae39d6` |
| `euler_unit_count_product_balance` | `a3514f1c5b92ba0b29541eb681b313f98d01a910aa26f25044e29fc13ebc6fbd` |
| `euler_coprime_totient_power_value` | `62401bc3ae6050ed789b54eb3028512546c4c3f927f19bda5ca6ce77dc293f55` |
| `euler_coprime_totient_power` | `4f3533b3d207055a1f56ca77655cf26a381735fa3999f34a0a2c7935a21497e4` |
| `euler_modular_unit_totient_power` | `9640b53a89a7ed7e2e15db573380a9a7133af60e7ebed2215390034354b4a4d6` |
| `euler_theorem_for_units` | `fcfb262cc347ec2cd7624dffba31f9ed519292b3ba5f1669682cee308cbac39d` |

## Verification and authority boundary

All 32 bodies have passed `candidate_validation.replay_candidate_bodies`
with the **unchanged original kernel**, against the authenticated v30
specification table plus the preceding local rows. Each positive and negative
proof replay runs in a fresh process, with the existing live proof limits,
an additional 45/50-second CPU guard, and a 60-second subprocess timeout.
The per-body node/depth/object metrics are pinned in the focused tests.
An additional fresh-process replay of all 32 bodies together passed in
11.474 seconds with a 382,468,096-byte peak RSS, within a 45/50-second CPU
guard and 55-second wall alarm. This measures candidate bodies, not the
separate closed proof checkpoint below.

Regressions reject false added conclusions, truncated scripts, removed
dependencies and corrupted dependency statements. Separate boundary
mutations reject replacing an actual unit by a merely nonzero residue,
removing coprimality, changing the exponent to `t+1`, replacing the real
unit-count relation by an oracle-like unconstrained count, and strengthening
the modulus-one conclusion to a false canonical-remainder claim. A separate
temporary original-kernel specialization explicitly checks the `m=1`,
`Phi(1,1)` endpoint; it is not counted as a new library row. Independent
numerical references explain the finite construction and its boundaries but
are not used as proof authority.

Run the three focused files separately, keeping each actual proof replay in
its bounded fresh subprocess:

```sh
PYTHONPATH=peano-lab/py:scripts python3 -m pytest -q peano-lab/py/tests/test_euler_units_residue_candidate.py
PYTHONPATH=peano-lab/py:scripts python3 -m pytest -q peano-lab/py/tests/test_euler_units_product_candidate.py
PYTHONPATH=peano-lab/py:scripts python3 -m pytest -q peano-lab/py/tests/test_euler_units_candidate.py
```

Final separate focused runs after deduplication: **155 passed in 25.72
seconds**, **185 passed in 29.61 seconds**, and **99 passed in 49.97 seconds**:
**439 distinct tests**, all three processes exiting successfully. These totals
include all 32 fresh-process positive body checks, 124 generic proof/dependency
mutations, three targeted corruptions of the reused parent dependencies,
five explicit boundary mutations, the genuine modulus-one specialization,
and 274 independent graph/hygiene/numerical/inventory contracts. The largest
measured test-controller peak RSS was 361,709,568 bytes, and the largest
single proof-subprocess peak was 393,691,136 bytes; these are separate process
measurements, not an aggregate simultaneous-memory measurement.

## Complete deduplicated proof checkpoint

The independently integrated v2 artifact is
`research/arithmetic-library/artifacts/bottom-layer-euler-units-proof-bundle-v2.json`:

- 210 closed nodes: 177 actual parent dependencies, 32 new rows, and one
  packaging node; 568 dependency edges and 12,452 body-node occurrences.
- 571,540 bytes; SHA-256
  `1edfcb7021a0869c2493383c75dea367d757be0b77f36fc6ad3f5fd18ed38210`.
- Every node passed the unchanged HA checker; the complete exact bundle also
  passed the independently compiled Lean checker.
- The export took 2.725 seconds, with peak RSS 472,301,568 bytes. Retained
  v1 bodies were freshly checked, and the two reused parent proofs came from
  authenticated sealed providers; an old receipt was not a proof premise.

Both principal Euler endpoints were also materialized as complete ordinary
HA certificates and rechecked in the empty context:

| Endpoint | Bundle node | Ordinary proof nodes |
| --- | ---: | ---: |
| `euler_theorem_for_units` | 208 | 17,918 |
| `euler_coprime_totient_power` | 206 | 17,610 |

The exact receipt is
`research/arithmetic-library/artifacts/bottom-layer-checkpoints-v2.json`.
The existing independent checker was identified by its actual 106,787,344-byte
binary and SHA-256
`22a49645acdee1a90bdf09861729d62b7a9c5bc20bc1f799ad05adc54ee0b033`;
it was not rebuilt in this tranche. Its acceptance is not inferred from a
toolchain label or a stored receipt. The integration's full parsed-AST audit
also compared every one of the 170 current bottom-layer statements with all
3,222 parent statements and with each other: no duplicate statements remain.

**Neither candidate replay nor this complete proof checkpoint is Alpha
admission.** Published Alpha remains 3,222 and Stable remains 432. This RFC
claims no promotion, publication, deployment, new axiom, or resource-limit
change. The superseded v1 bytes remain intact.
