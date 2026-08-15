# RFC HA-R6-BERTRAND-PRIMORIAL-1: filtered primorial foundation

**Status:** binding subordinate statement, representation, dependency,
evidence, trust, capacity, and release contract; no theorem is enrolled or
admitted by this document

**Parent campaign:**
[`RFC HA-R6-BERTRAND-1`](ha-bertrand-postulate-campaign-rfc-v1.md), SHA-256
`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`

**Representation amendment:**
[`RFC HA-R6-BERTRAND-2`](ha-bertrand-postulate-campaign-rfc-v2.md), SHA-256
`af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`

**Immutable edition parent:** Alpha v8 at commit
`06274fbe3c4e20281cd904f3e1dd1a6f36ed4544`

**Object language:** unchanged first-order HA over
\(\{0,S,+,\times,=\}\)

**Kernel change:** none

**Classical axioms:** none

This RFC freezes the first ten-row B4 foundation microbatch after Alpha v8.
It defines a filtered primorial conservatively by multiplying one selected
factor at each candidate position: candidate `S i` itself when it is prime,
and the neutral factor `1` otherwise. The resulting product contains every
prime at most `m` exactly once and no other nonunit factor.

The words **must**, **must not**, **should**, and **may** are normative. In a
conflict, the two parent RFCs control the campaign endpoint, logic, trust, and
promotion policy; this document controls the ten row names, statement
surfaces, order, direct dependencies, representation, and subordinate gates.

## 1. Scope and non-claims

This tranche supplies:

1. constructive existence and functionality of the factor selected at one
   candidate index;
2. existence, extension, and extensional transport for beta-coded prefixes
   of selected factors;
3. a conservative authoring-only `Primorial(m,z)` relation;
4. totality and functionality of that relation;
5. its zero and one-step decomposition laws; and
6. constructive positivity as an explicit successor witness.

This tranche does **not** complete B4. In particular, it does not yet provide
the two directions of prime membership/divisibility, general monotonicity,
filtered interval products, interval splitting, comparison with an arbitrary
duplicate-free bounded prime product, or `primorial_le_four_pow`. It does not
provide a B5 central-binomial upper bound, a B7 or B8 theorem, BP01, or BP02.
It creates no Alpha membership, checked-use grant, Stable membership,
publication, or deployment.

`Prime`, `Lt`, `BetaAt`, `Product`, `Sel`, `FactorPrefix`, and `Primorial` are
authoring notation only. Every occurrence must expand hygienically into the
unchanged first-order language before parsing. No prime predicate, list,
finite set, filter, product, recursion principle, formula constructor,
normalizer, or arithmetic axiom is added to the parser or kernel.

## 2. Immutable Alpha-v8 parent

The sole edition parent is the sealed Alpha-v8 snapshot at commit
`06274fbe3c4e20281cd904f3e1dd1a6f36ed4544`:

- theorem count: `1055`;
- declared direct-edge count: `3224`;
- dependency-layer count: `45`;
- checked-use count: `570`;
- evidence counts: `432 stable_closed`, `138 alpha_closed`,
  `484 body_checked`, and `1 pending_layered_closure`;
- ordered enrollment root:
  `a01b0224be070b09551c6ef7b50f9c32688448f48465b80ca97a23c01effd5c2`;
- ordered specification root:
  `fe49d664e5a88f6637c7790b104e9b0aa3c583e48f9a4a1405d5b098f7f61df9`;
- edition identity:
  `2101b7b384ec9791c41d07d8115123d6842729615a0084ce87cead619bc8c123`;
- membership root:
  `4471bdcf06a2d3af866850b39f394a436ad608b4c0b166c0449620e5dd3c9ee3`;
- evidence root:
  `4230c17701be2c604ea413be90c26bad41889d593dcaaeff311217b4e26367b4`;
- channel-pointer root:
  `1fd2216e0448fbeb0d8da60dea3b89fca4d4f7192371fc87a8c5cd35dccf3c70`;
- Alpha catalog artifact SHA-256:
  `c06c5fde7b84b4a8524dd408a2b046d06c7a88ccb5814877b7ccfec0d20b1370`;
- Alpha metrics artifact SHA-256:
  `90c14911ef50391dd9fd99865a83a6e0886911253504096a30e497d30c1a6813`;
- Alpha graph artifact SHA-256:
  `ff194534f1efd56dd771237b6a44279a705309df21c1fa319b6669f3e1cab008`;
  and
- channel artifact SHA-256:
  `dec01b10ee9359b1f7057187725016d343bfb7f3176d8779c85da7f26983234d`.

No implementation of this RFC may edit an Alpha-v1 through Alpha-v8 ledger,
artifact, root, pointer, canonical position, origin, or evidence record.
Stable v1 remains the unchanged 432-row checked edition and default channel.
A future edition must preserve all 1055 Alpha-v8 entries byte-for-byte and in
their existing order before appending any row below.

Every external direct dependency in Section 5 is already `stable_closed` in
Stable v1. Candidate-only product-order and prefix/suffix-splitting rows are
not dependencies of this foundation. The thirty-eight Alpha-v8
Choose/central-binomial rows remain `body_checked`; later use of them by
`primorial_le_four_pow` must recursively close them or consume a separately
sealed checked-use upgrade. Their enrollment is not theorem authority.

## 3. Frozen conservative representation

The prime surface is exactly the existing expanded convention

```text
Prime(q) :=
  ~(q = 1) /\
  forall a d. q = a * d -> a = 1 \/ d = 1
```

For an index `i` and selected factor `p`, freeze

```text
Sel(i,p) :=
  (Prime(S i) /\ p = S i) \/
  (~Prime(S i) /\ p = 1)
```

For a beta code `b`, scale `c`, and length `m`, freeze

```text
FactorPrefix(b,c,m) :=
  forall i. Lt(i,m) ->
    exists p. BetaAt(b,c,i,p) /\ Sel(i,p)
```

Finally, freeze

```text
Primorial(m,z) :=
  exists b c.
    FactorPrefix(b,c,m) /\ Product(b,c,m,z)
```

All displayed connectives, quantifiers, `Lt`, `BetaAt`, and `Product` must be
fully expanded before parsing. Generated binders must avoid every free name
in the supplied terms and every binder owned by an enclosing expansion.
Term-capable internal builders must parse terms in an explicit context and
pretty-print the parsed AST; unchecked string substitution is forbidden.

The indexing convention is binding. `FactorPrefix(b,c,m)` has indices
`i<m`, so its candidates are `1,2,...,m`. Thus `Primorial(m,z)` denotes the
inclusive mathematical primorial \(\prod_{p\le m}p\). The value at candidate
`1` is the neutral factor because `Prime(1)` is false. Neutral placeholders
are a conservative encoding device, not members of a prime-only list.

The representation deliberately avoids a filtered-list count, raw-code
uniqueness, and choice. It also makes each prime candidate occur at one index,
so duplicates cannot arise inside `Primorial`. A later theorem comparing an
external prime-only product must still state and prove that external
product's duplicate-free condition.

## 4. Frozen occurrence tags and byte-seal boundary

The following occurrence tags are binding inputs to the hygienic builders:

| Row | Frozen occurrence tags |
|---|---|
| `primorial_factor_choice_exists` | `bpfc_exists` |
| `primorial_factor_choice_functional` | `bpfcf_left`, `bpfcf_right` |
| `primorial_factor_prefix_extend` | `bpfpe_before`, `bpfpe_after` |
| `primorial_factor_prefix_exists` | `bpfpx_result` |
| `primorial_factor_prefix_transport_entry` | `bpfpt_left`, `bpfpt_right` |
| `primorial_exists` | `bp_exists` |
| `primorial_functional` | `bp_functional_left`, `bp_functional_right` |
| `primorial_zero` | `bp_zero_source` |
| `primorial_succ_decompose` | `bp_succ_source`, `bp_succ_predecessor`, |
| | `bp_succ_factor` |
| `primorial_positive` | `bp_positive_source` |

The logical contract and these tags are binding now. Candidate source path,
focused-test path, source SHA-256, test SHA-256, expanded statement hashes,
script hashes, artifact tuples, body/envelope receipts, and closure receipts
are **to be filled from the landed candidate and its fail-closed focused
test**. This RFC does not invent or pre-authorize those byte seals. Once
recorded in a reviewed successor evidence section or enrollment manifest,
changing any binder order, association, tag, dependency order, statement, or
tactic command requires a versioned successor contract.

## 5. Exact theorem order, surfaces, and direct dependencies

The order below is immutable. `Prime`, `Sel`, `FactorPrefix`, `Primorial`,
`Lt`, `BetaAt`, and `Product` stand only for the exact expansions in Section 3
and the inherited fold surface.

1. `primorial_factor_choice_exists`

   ```text
   forall i. exists p. Sel(i,p)
   ```

   Direct dependencies, in exact order:
   `prime_decidable`.

2. `primorial_factor_choice_functional`

   ```text
   forall i p q. Sel(i,p) -> Sel(i,q) -> p = q
   ```

   Direct dependencies: none.

3. `primorial_factor_prefix_extend`

   ```text
   forall b c m.
     FactorPrefix(b,c,m) ->
     exists d e. FactorPrefix(d,e,S m)
   ```

   Direct dependencies, in exact order:
   `primorial_factor_choice_exists`, `beta_prefix_extend`,
   `finite_lt_succ_eq_or_lt`.

4. `primorial_factor_prefix_exists`

   ```text
   forall m. exists b c. FactorPrefix(b,c,m)
   ```

   Direct dependencies, in exact order:
   `add_eq_zero_right`, `succ_ne_zero`,
   `primorial_factor_prefix_extend`.

5. `primorial_factor_prefix_transport_entry`

   ```text
   forall b c d e m.
     FactorPrefix(b,c,m) -> FactorPrefix(d,e,m) ->
     forall i p.
       Lt(i,m) -> BetaAt(b,c,i,p) -> BetaAt(d,e,i,p)
   ```

   Direct dependencies, in exact order:
   `beta_at_unique`, `primorial_factor_choice_functional`.

6. `primorial_exists`

   ```text
   forall m. exists z. Primorial(m,z)
   ```

   Direct dependencies, in exact order:
   `beta_product_exists`, `primorial_factor_prefix_exists`.

7. `primorial_functional`

   ```text
   forall m x y.
     Primorial(m,x) -> Primorial(m,y) -> x = y
   ```

   Direct dependencies, in exact order:
   `beta_product_transport_prefix`, `beta_product_functional`,
   `primorial_factor_prefix_transport_entry`.

8. `primorial_zero`

   ```text
   forall z. Primorial(0,z) -> z = 1
   ```

   Direct dependencies, in exact order:
   `beta_product_zero`.

9. `primorial_succ_decompose`

   ```text
   forall m z.
     Primorial(S m,z) ->
     exists p r.
       Sel(m,p) /\ (Primorial(m,r) /\ z = r * p)
   ```

   Direct dependencies, in exact order:
   `beta_product_succ_decompose`, `beta_at_unique`, `le_refl`, `le_succ`.

   This generic selected-factor recurrence is binding. It must not be
   replaced by a branch-simplified equation, and it has no `mul_one`
   dependency.

10. `primorial_positive`

    ```text
    forall m z. Primorial(m,z) -> exists r. z = S r
    ```

    Direct dependencies, in exact order:
    `mul_succ_left`, `primorial_zero`, `primorial_succ_decompose`.

No dependency may be silently added because it is convenient, transitively
available, enrolled in Alpha, or present in a candidate provider. Removing
any listed edge must make the focused liveness gate fail.

## 6. Required proof topology

The intended proof architecture is part of the review boundary:

1. Factor choice cases only on `prime_decidable (S i)` and chooses `S i` in
   the prime branch and `1` in the refutation branch.
2. Choice functionality cases both `Sel` hypotheses. Same-branch equations
   close directly; mixed branches close from the explicit prime/refutation
   contradiction. It has no theorem dependency.
3. Prefix extension obtains the terminal choice, uses one
   `beta_prefix_extend`, and uses `finite_lt_succ_eq_or_lt` to separate the
   terminal index from the preserved old prefix.
4. Prefix existence is induction on `m`. Its zero branch proves the bounded
   universal vacuously from `add_eq_zero_right` and `succ_ne_zero`; its
   successor branch uses only row 3.
5. Entry transport extracts the selected value from both prefixes, aligns an
   arbitrary decoded source value by `beta_at_unique`, applies row 2, and
   returns the target decoded entry. It must not assume equality of raw beta
   codes.
6. Primorial existence combines a selected prefix with
   `beta_product_exists` on that exact factor code and scale.
7. Primorial functionality transports one `Product` extensionally onto the
   second factor encoding and then applies `beta_product_functional`. It must
   not use raw-code equality or an arbitrary provider scan.
8. The zero row is the direct `beta_product_zero` projection.
9. Successor decomposition uses `beta_product_succ_decompose`, aligns its
   decoded terminal factor with the prefix selector by `beta_at_unique`, and
   restricts the selected prefix with `le_succ`. The exact output is the
   generic factor `p` and predecessor value `r` displayed in Section 5.
10. Positivity inducts on `m`, uses row 8 at zero, and in the successor branch
    cases the `Sel(m,p)` evidence from row 9 directly. In both selector
    branches `p` is a successor; `mul_succ_left` and primitive `PA4` construct
    the successor result. The proof must not first construct an
    `OrElim`-rooted existential and then eliminate it, and must not add DNE or
    a nonzero-product oracle.

All locally constructed values that will later be eliminated must have an
inferable proof source. A `LocalHave` whose substituted source begins with an
eliminator that the independent kernel cannot synthesize is rejected even if
the tactic engine closes every goal.

## 7. Focused evidence and authority boundary

The candidate implementation must have one focused fail-closed test. That
test must independently rebuild every expanded surface from pinned authoring
helpers; importing a production statement constant is not independent
evidence. It must pin every source file whose factory it executes, including
the candidate source itself.

For each row, replay authority is exactly Stable plus the earlier local prefix
listed in Section 5. A row must not obtain theorem authority from:

- a later sibling;
- an arbitrary candidate-provider scan;
- Alpha membership alone;
- `body_checked` evidence;
- a statement, body, artifact, or closure receipt; or
- any B7, B8, BP01, or BP02 theorem.

Provider, Stable, Alpha, and edition-name collisions must fail closed. The
test must assert that none of the ten names is already present in the parent
edition or a production authority registry. This RFC and its tests are
evidence providers, not theorem registries.

Before any possible enrollment, every row must have concrete:

```text
(statement_length,
 sha256(expanded_statement),
 sha256(NUL-joined tactic script),
 sha256(NUL-joined expanded statement and direct dependencies))
```

plus body, proof-envelope, and independently kernel-accepted empty-context
closure receipts. `None`, placeholder text, a source hash in place of a proof
receipt, or a receipt computed before a semantic gate is fail-closed.

## 8. Mutation contract

The focused test must run structural, semantic, and kernel mutations before
accepting any receipt. At minimum it must include:

- removal of every direct dependency, one edge at a time;
- conjunction with `false` for every target;
- invalid identifier, invalid tag, generated-binder collision, omitted free
  variable, and binder-capture cases for every private builder family;
- a selector mutation deleting the nonprime branch, refuted at candidate
  `1`, and one deleting the prime branch, refuted at candidate `2`;
- a choice-functionality conclusion `p = S q`, refuted by two choices of
  candidate `1`;
- a prefix-extension mutation that fixes the output to the unre-encoded
  source code, with a concrete positive-length counterfixture;
- a prefix-existence mutation that additionally decodes `0` at the first
  in-range position, refuted at length `1`;
- a transport mutation changing the target value from `p` to `S p`, refuted
  at the candidate-`1` prefix;
- a primorial-existence mutation forcing `z = 0`, refuted at `m = 0`;
- a functionality conclusion `x = S y`, refuted at `m = 0`;
- a zero conclusion `z = 0`;
- a successor mutation changing `Sel(m,p)` to `Sel(S m,p)` or changing the
  predecessor occurrence to `Primorial(S m,r)`, with a checked small
  counterfixture; and
- positivity strengthened to `exists r. z = S (S r)`, refuted by
  `Primorial(0,1)`.

Mutations that merely alpha-rename a binder, commute a true equality, or
replace a theorem by another true statement do not count as genuine boundary
evidence. Every mutation must identify its unique source substring and a
small mathematical counterfixture.

The closure gate must count the exact direct `Cut` spine for each row and
corrupt every direct `Cut`, not a first/middle/last sample. Every corruption
must be rejected by the independent kernel before the closure receipt is
compared.

## 9. Capacity and crash-safety contract

The current campaign limits remain unchanged:

- at most `4096` candidate proof nodes during body replay;
- at most `65536` candidate body edges;
- at most `500000` empty-context proof occurrences;
- at most `100000` distinct empty-context proof objects;
- maximum proof depth `256`; and
- at most `5000000` annotation occurrences.

Limits are resource policy, not logical rules. They must not be increased for
this tranche. If a row misses a limit, first reduce its direct dependencies,
factor a reusable theorem, or localize large equality motives.

Run body, mutation, and closure selectors serially in fresh processes with
memory observed. A timeout does not cap resident memory. Concurrent proof
workers and a monolithic retained-DAG run are not approved laptop gates.
Formula/envelope traversal must be bounded before any unbounded diagnostic
walk. Hashes are receipts, not semantic checks.

## 10. Initial evidence status and later promotion

If a future Alpha successor enrolls these rows after all gates pass, each
must initially have exactly:

```text
membership = alpha_only
evidence = body_checked
checked_use = false
proof_tag = null
empty_context_closure = null
```

This RFC itself performs no enrollment. Focused test success and an
empty-context candidate closure do not independently grant checked use,
`alpha_closed`, or Stable membership. Evidence may be upgraded only in a new
append-only artifact after two cold fresh-process passes and independent
review. Stable promotion requires a separately reviewed dependency-closed
subset and must preserve enrollment origin, provenance, source, statement,
dependency order, script, and canonical Alpha position.

## 11. Required later B4 tranches

The ten rows are a foundation, not a completion claim. A binding successor
RFC or versioned extension must freeze the remaining work in dependency order.

### 11.1 Prime divisibility characterization

Prove both directions, then the exact equivalence:

```text
Prime(p) -> Le(p,m) -> Primorial(m,z) -> exists q. z = p * q

Prime(p) -> Primorial(m,z) -> (exists q. z = p * q) -> Le(p,m)
```

The forward direction should decode candidate `p` from its unique index and
use the stable `beta_factor_divides_product`. The reverse direction requires
induction through row 9 and Euclid's prime-divides-product theorem; the
existing `beta_prime_divisor_product_member` cannot be applied directly
because a selected prefix intentionally contains neutral `1` entries.

### 11.2 Monotonicity

First prove one-step and general divisibility monotonicity, then derive the
numeric order using positivity and the checked divisor bound. Do not assume
that beta codes at different bounds are equal.

### 11.3 Filtered intervals and splitting

Freeze an offset filtered-product relation covering candidates
`a+1,...,a+l`, using selector candidate `S (a + i)`. Prove its totality and
functionality, then split a primorial at an arbitrary bound into prefix and
offset interval products. The existing candidate-only
`beta_product_prefix_suffix_split` may be independently pinned and reviewed
in that later tranche, or the split may be proved semantically by recurrence;
it is not authority for the present ten rows.

### 11.4 Duplicate-free bounded products

Freeze an explicit duplicate-free condition for an external beta-coded
prime-only product. Existing adjacent `Sorted` is weak order and permits
duplicates, so it is not sufficient by itself. Prove that every such bounded
product divides the corresponding primorial, then use positivity to obtain
the required comparison.

### 11.5 Primorial bound

Only after the necessary elementary central-binomial upper clients are
closed may the campaign prove:

```text
Primorial(m,z) -> Pow(4,m,q) -> Le(z,q)
```

The exact final surface may include explicit totality witnesses if required
by the recurrence proof, but it must retain the mathematical content
\(m\#\le4^m\). Its closure may depend on B3 and earlier rows only. The test
must machine-reject injected edges to B7, B8, BP01, BP02, or any theorem
equivalent to Bertrand's postulate.

## 12. Acceptance checklist

The foundation is ready for an initial body-only enrollment proposal only
when:

- [ ] the parent RFC hashes, Alpha-v8 commit, counts, and roots match
      Sections 1 and 2;
- [ ] the landed source and focused test fill every pending byte seal without
      changing Sections 3--6;
- [ ] exact expanded statements, scripts, dependency order, and artifact
      identities reproduce in a clean process;
- [ ] every direct dependency exists in Stable or the earlier local prefix;
- [ ] every dependency-removal, false-target, genuine-boundary, hygiene,
      collision, capture, and direct-`Cut` mutation fails closed;
- [ ] every body, envelope, and closure is accepted by the ordinary
      intuitionistic kernel with zero `DNE` and current caps;
- [ ] no B7, B8, BP01, or BP02 edge occurs; and
- [ ] all Alpha-v1 through Alpha-v8 and Stable artifacts remain unchanged.

Passing this checklist establishes only the ten-row foundation evidence. It
does not pass B4 and does not establish Bertrand's postulate.
