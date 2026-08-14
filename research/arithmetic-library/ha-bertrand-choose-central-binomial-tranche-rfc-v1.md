# RFC HA-R6-BERTRAND-CB-1: Choose and central-binomial tranche

**Status:** binding subordinate statement, evidence, trust, capacity, and
release contract; no theorem is enrolled or admitted by this document

**Parent campaign:**
[`RFC HA-R6-BERTRAND-1`](ha-bertrand-postulate-campaign-rfc-v1.md), SHA-256
`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`

**Representation amendment:**
[`RFC HA-R6-BERTRAND-2`](ha-bertrand-postulate-campaign-rfc-v2.md), SHA-256
`af5ab20980b32f31d3a6ad5f3f041c64b3d359489b50114733da3c4d2f1618`

**Object language:** unchanged first-order HA over
\(\{0,S,+,\times,=\}\)

**Kernel change:** none

**Classical axioms:** none

**Candidate freeze:** commits `d46e513` through `74dc219`, inclusive, with
parent tree `59444e2` and terminal commit
`74dc219e03e766436f9feae90b9af238fb35efcd`

This RFC freezes the exact post-Alpha-v7 recurrence-first `Choose` and
`CentralBinom` layer. It contains nineteen candidate modules, nineteen focused
tests, and thirty-eight theorem rows. The rows are split into one
twenty-four-row foundation microbatch and one fourteen-row recurrence and
growth microbatch. The split satisfies the parent RFC's ten-to-twenty-five-row
validation envelope without hiding the dependency boundary between the two
parts.

The words **must**, **must not**, **should**, and **may** are normative. In a
conflict, the parent RFCs control endpoint, logic, and promotion policy; this
document controls the thirty-eight-row identities, order, local architecture,
and subordinate gates.

## 1. Scope and non-claims

This tranche supplies:

1. a recurrence-defined finite Pascal table and relational `Choose` surface;
2. extensional row and table functionality across different beta encodings;
3. zero, diagonal, Pascal, symmetry, and positivity laws for `Choose`;
4. the authoring-only relation
   `CentralBinom(n,z) := Choose(n + n,n,z)`;
5. central-binomial zero and successor laws;
6. the complement-form factorial bridge;
7. the weighted central recurrence; and
8. the lower bound `four_pow_lt_mul_central_binom`.

`Choose`, `CentralBinom`, Pascal rows and tables, `Factorial`, `Pow`, weak
order, and strict order are authoring notation only. Every occurrence must be
expanded hygienically to the unchanged first-order language before parsing.
No new formula constructor, recursion principle, arithmetic axiom, trusted
normalizer, quotient operation, or sequence object is introduced.

This RFC does **not** prove Bertrand's postulate. It does not provide the
primorial or prime-range upper-bound half of B4/B5, and it does not admit BP01
or BP02. It also creates no Alpha membership, checked-use grant, Stable
membership, browser publication, or deployment.

## 2. Immutable parent edition

The sole edition parent is sealed Alpha v7:

- theorem count: `1017`;
- enrollment root:
  `aaabe990d13d46b29e5f7c20f928e6ce3353c05ccf8dec51041243a7cd79534c`;
- ordered specification root:
  `838c8f48f81eddcdf3e9de0f9557cee1c25eb78015513d99cfe8ab76975edc65`;
- edition identity:
  `9afc0f00c01ce2c82f77f59ec674f0273462c31f8238943ec879e757111cc5ff`;
- membership root:
  `e6d22473986c7e4ec1e4566f156c3dad710a4a9be2ae7b830490546da48cb703`;
- evidence root:
  `a3709e040891b7c180c5c35876ec0e033b58ad12ce5179c3b0215ed11c1a93b6`;
- channel-pointer root:
  `e868088b8abf7b98e1a3976058adfca5ed542a1d9b29c275ebd16c070cd810c3`.

No implementation of this RFC may edit an Alpha-v1 through Alpha-v7 ledger,
artifact, root, channel pointer, origin, or evidence record. Stable v1 remains
the unchanged 432-row checked edition. A later edition must preserve all 1017
Alpha-v7 entries byte-for-byte and in their existing order before appending
any row below.

All external direct dependencies of the thirty-eight rows occur as
specifications in Alpha v7. All are `stable_closed` except
`two_mul_eq_add_self`, which is `body_checked`. Consequently, a future
empty-context closure or promotion batch containing row 29 must also close
`two_mul_eq_add_self` or consume a separately sealed checked-use upgrade. Its
presence as an Alpha specification is not checked-use authority.

## 3. Exact statement and artifact identity

The exact expanded statement, variable order, dependency order, tactic script,
and logical identity for each row are the values frozen in the corresponding
focused test at commit `74dc219`. In every test, the canonical artifact tuple
is:

```text
(statement_length,
 sha256(expanded_statement),
 sha256(NUL-joined tactic script),
 sha256(NUL-joined expanded statement and direct dependencies))
```

Every tuple is concrete in the frozen tests. An enrollment implementation must
reconstruct the candidate factories from the pinned sources and reproduce
those tuples exactly. A hash comparison is a receipt, not semantic evidence;
formula parsing, dependency-curried checking, and empty-context kernel checking
remain mandatory.

The following surface conventions are frozen:

- `Choose(n,k,z)` is the fully expanded relation produced by
  `bertrand_choose_foundation_candidate.py` at source SHA
  `97307689cedbb28c13dd296ac47d86f052e947ef1cf18f7c9a6f2cf27499c17d`;
- `CentralBinom(n,z)` is exactly `Choose(n + n,n,z)`, with carrier `n + n` in
  that order and association;
- factorial bridge multiplication remains in the frozen complement form
  `F = (K * J) * c`;
- the weighted vertical theorem retains its frozen complement equation and
  product orientation; and
- the lower bound retains the public row name and exact relation-expanded
  surface ending in the strict inequality \(4^n<nC_n\) for `4 <= n`.

Changing a binder order, helper tag, multiplication association, `n + n`
carrier, dependency order, or tactic command changes the frozen artifact and
requires a versioned successor RFC. Alpha-renaming of internal generated
binders is not a license to change the public expanded bytes.

## 4. Pinned module ledger

The source and focused test in each item landed together at the listed commit.
The commit tree, the source SHA pinned by its test, and the test's own concrete
artifact/body/envelope/closure receipts jointly bind the bytes.

### Microbatch A: rows 1--24

1. `d46e513`:
   `bertrand_choose_foundation_candidate.py` and
   `test_bertrand_choose_foundation_candidate.py`, rows 1--7.
2. `f21ab6a`:
   `bertrand_choose_row_functional_candidate.py` and
   `test_bertrand_choose_row_functional_candidate.py`, rows 8--9.
3. `f62d8c3`:
   `bertrand_choose_table_row_functional_candidate.py` and
   `test_bertrand_choose_table_row_functional_candidate.py`, row 10.
4. `6f77674`:
   `bertrand_choose_laws_candidate.py` and
   `test_bertrand_choose_laws_candidate.py`, rows 11--13.
5. `e9525d0`:
   `bertrand_choose_diagonal_candidate.py` and
   `test_bertrand_choose_diagonal_candidate.py`, rows 14--15.
6. `0995093`:
   `bertrand_choose_recurrence_candidate.py` and
   `test_bertrand_choose_recurrence_candidate.py`, rows 16--17.
7. `928a5fd`:
   `bertrand_choose_pascal_candidate.py` and
   `test_bertrand_choose_pascal_candidate.py`, row 18.
8. `dbcc90f`:
   `bertrand_choose_symmetry_candidate.py` and
   `test_bertrand_choose_symmetry_candidate.py`, rows 19--20.
9. `16e2284`:
   `bertrand_choose_positive_candidate.py` and
   `test_bertrand_choose_positive_candidate.py`, row 21.
10. `b237acb`:
    `bertrand_central_binom_candidate.py` and
    `test_bertrand_central_binom_candidate.py`, rows 22--24.

### Microbatch B: rows 25--38

11. `6d3b494`:
    `bertrand_central_binom_zero_candidate.py` and
    `test_bertrand_central_binom_zero_candidate.py`, row 25.
12. `2de1a11`:
    `bertrand_central_binom_succ_candidate.py` and
    `test_bertrand_central_binom_succ_candidate.py`, rows 26--27.
13. `a312eff`:
    `bertrand_choose_weighted_vertical_candidate.py` and
    `test_bertrand_choose_weighted_vertical_candidate.py`, row 28.
14. `dadbe92`:
    `bertrand_central_binom_recurrence_candidate.py` and
    `test_bertrand_central_binom_recurrence_candidate.py`, row 29.
15. `d493f7e`:
    `bertrand_choose_factorial_support_candidate.py` and
    `test_bertrand_choose_factorial_support_candidate.py`, rows 30--31.
16. `7c7a9da`:
    `bertrand_choose_factorial_bridge_candidate.py` and
    `test_bertrand_choose_factorial_bridge_candidate.py`, row 32.
17. `b5d2ba4`:
    `bertrand_central_binom_growth_candidate.py` and
    `test_bertrand_central_binom_growth_candidate.py`, rows 33--34.
18. `41f689c`:
    `bertrand_central_binom_lower_seed_candidate.py` and
    `test_bertrand_central_binom_lower_seed_candidate.py`, rows 35--37.
19. `74dc219`:
    `bertrand_central_binom_lower_bound_candidate.py` and
    `test_bertrand_central_binom_lower_bound_candidate.py`, row 38.

All paths are relative to `peano-lab/py/peano_lab/library/` for sources and
`peano-lab/py/tests/` for tests. No unlisted factory output belongs to this
tranche.

## 5. Dependency-topological theorem manifest

The order below is immutable. Dependencies are listed in exact direct order.
Names not defined earlier in this manifest are inherited Alpha-v7
specifications and must be resolved by exact name and logical identity.

### Microbatch A: recurrence-defined Choose and central wrappers

1. `beta_pascal_zero_row_extend`
   - dependencies: `zero_or_succ`, `beta_prefix_extend`,
     `finite_lt_succ_eq_or_lt`.
2. `beta_pascal_zero_row_exists`
   - dependencies: `add_eq_zero_right`, `succ_ne_zero`,
     `beta_pascal_zero_row_extend`.
3. `beta_pascal_row_step_extend`
   - dependencies: `zero_or_succ`, `beta_at_exists`,
     `beta_prefix_extend`, `finite_lt_succ_eq_or_lt`.
4. `beta_pascal_row_step_exists`
   - dependencies: `add_eq_zero_right`, `succ_ne_zero`,
     `beta_pascal_row_step_extend`.
5. `beta_pascal_table_prefix_extend`
   - dependencies: `zero_or_succ`, `le_refl`, `lt_to_le`,
     `beta_prefix_extend`, `finite_lt_succ_eq_or_lt`,
     `beta_pascal_zero_row_exists`, `beta_pascal_row_step_exists`.
6. `beta_pascal_table_prefix_exists`
   - dependencies: `add_eq_zero_right`, `succ_ne_zero`,
     `beta_pascal_table_prefix_extend`.
7. `choose_exists`
   - dependencies: `le_or_lt`, `beta_at_exists`,
     `beta_pascal_table_prefix_exists`.
8. `beta_pascal_zero_row_pointwise_functional`
   - dependencies: `beta_at_unique`, `succ_ne_zero`.
9. `beta_pascal_row_step_pointwise_functional`
   - dependencies: `beta_at_unique`, `succ_ne_zero`, `succ_injective`,
     `lt_to_le`.
10. `beta_pascal_table_row_pointwise_functional`
    - dependencies: `beta_at_unique`, `succ_ne_zero`, `succ_injective`,
      `lt_to_le`, `beta_pascal_zero_row_pointwise_functional`,
      `beta_pascal_row_step_pointwise_functional`.
11. `choose_functional`
    - dependencies: `lt_not_le`, `le_refl`, `succ_le_succ`,
      `beta_pascal_table_row_pointwise_functional`.
12. `choose_out_of_range_zero`
    - dependencies: `lt_not_le`.
13. `choose_zero`
    - dependencies: `zero_le`, `lt_not_le`, `le_refl`, `succ_le_succ`,
      `succ_ne_zero`, `beta_at_unique`.
14. `beta_pascal_table_diagonal_boundary`
    - dependencies: `add_eq_zero_right`, `succ_ne_zero`,
      `succ_injective`, `le_of_succ_le_succ`, `lt_to_le`, `le_refl`,
      `beta_at_unique`.
15. `choose_self`
    - dependencies: `lt_irrefl_expanded`, `le_refl`,
      `beta_pascal_table_diagonal_boundary`.
16. `beta_pascal_table_successor_cell_recurrence`
    - dependencies: `beta_at_unique`, `succ_ne_zero`, `succ_injective`.
17. `choose_succ_succ_of_lt`
    - dependencies: `lt_not_le`, `lt_to_le`, `le_refl`, `le_succ`,
      `succ_le_succ`, `beta_pascal_table_row_pointwise_functional`,
      `beta_pascal_table_successor_cell_recurrence`.
18. `choose_succ_succ`
    - dependencies: `lt_trichotomy`, `le_refl`, `le_succ`,
      `succ_le_succ`, `choose_out_of_range_zero`, `choose_self`,
      `choose_succ_succ_of_lt`.
19. `choose_self_of_eq`
    - dependencies: `choose_self`.
20. `choose_symmetry`
    - dependencies: `zero_add`, `add_succ_left`, `add_comm`,
      `choose_exists`, `choose_zero`, `choose_self_of_eq`,
      `choose_succ_succ`.
21. `choose_positive`
    - dependencies: `le_zero`, `le_of_succ_le_succ`, `add_succ_left`,
      `choose_exists`, `choose_zero`, `choose_succ_succ`.
22. `central_binom_exists`
    - dependencies: `choose_exists`.
23. `central_binom_functional`
    - dependencies: `choose_functional`.
24. `central_binom_positive`
    - dependencies: `choose_positive`.

### Microbatch B: central recurrence, bridge, and lower bound

25. `central_binom_zero`
    - dependencies: `choose_zero`.
26. `choose_upper_eq_transport`
    - dependencies: none.
27. `central_binom_succ_double_middle`
    - dependencies: `add_succ_left`, `choose_exists`, `choose_symmetry`,
      `choose_succ_succ`, `choose_upper_eq_transport`.
28. `choose_weighted_vertical`
    - dependencies: `zero_or_succ`, `zero_add`, `add_succ_left`,
      `add_assoc`, `mul_succ_left`, `mul_add`, `choose_exists`,
      `choose_zero`, `choose_self_of_eq`, `choose_succ_succ`.
29. `central_binom_succ_recurrence`
    - dependencies: `mul_add`, `mul_assoc`, `two_mul_eq_add_self`,
      `central_binom_succ_double_middle`, `choose_weighted_vertical`.
30. `factorial_length_eq_transport`
    - dependencies: none.
31. `factorial_weighted_product_combine`
    - dependencies: `mul_comm`, `mul_assoc`.
32. `choose_factorial_bridge`
    - dependencies: `mul_one`, `choose_exists`, `choose_self_of_eq`,
      `choose_weighted_vertical`, `factorial_functional`,
      `factorial_zero`, `factorial_succ_decompose`,
      `factorial_length_eq_transport`,
      `factorial_weighted_product_combine`.
33. `mul_lt_mul_right_nonzero`
    - dependencies: `mul_comm`, `mul_lt_mul_succ_left_nonzero`,
      `mul_le_mul_right`, `lt_of_lt_of_le`.
34. `four_power_central_recurrence_step`
    - dependencies: `add_eq_zero_right`, `add_comm`, `mul_comm`,
      `mul_assoc`, `mul_add`, `add_mul`, `mul_lt_mul_right_nonzero`,
      `lt_trans`.
35. `pow_four_four_exact`
    - dependencies: `pow_successor_decompose`, `pow_two`.
36. `central_binom_four_weighted_of_recurrence`
    - dependencies: `one_mul`, `mul_left_cancel_nonzero`,
      `central_binom_zero`.
37. `four_pow_central_seed_package`
    - dependencies: `mul_assoc`, `mul_lt_mul_right_nonzero`,
      `central_binom_exists`, `pow_four_four_exact`,
      `central_binom_four_weighted_of_recurrence`.
38. `four_pow_lt_mul_central_binom`
    - dependencies: `lt_not_le`, `pow_successor_decompose`,
      `central_binom_succ_recurrence`,
      `four_power_central_recurrence_step`,
      `four_pow_central_seed_package`.

The apparent omission of recurrence and central-existence dependencies from
row 36 is intentional: its frozen theorem surface takes those data as explicit
premises. Row 37 packages the needed existence premise and shares the single
recurrence hypothesis used by its clients. An enrollment adapter must not turn
those explicit premises into hidden authority edges.

## 6. Microbatch boundary and authority discipline

Microbatch A is independently authorable and enrollable. Microbatch B may be
enrolled only after all twenty-four A rows occupy the exact preceding Alpha
positions. The permitted release shapes are:

1. one additive Alpha successor containing A followed by B, with separate
   validation receipts for the two microbatches; or
2. an A-only additive Alpha successor followed by a later additive successor
   that preserves A exactly and appends B.

B-before-A enrollment, interleaving, omission of an interior row, or insertion
of an unrelated row inside either frozen sequence is forbidden. If an unrelated
edition append lands first, this RFC reserves no historical version number;
the next implementation must use the then-current immutable Alpha successor
while preserving this exact local order.

Candidate factories and focused tests are evidence providers, not theorem
authority. A row test may resolve Stable/Alpha-v7 specifications and only the
earlier local prefix explicitly intended for that row. It must not consume a
later sibling, scan arbitrary candidate modules, or use a receipt as a theorem.
The enrollment manifest must rebuild every selected factory from its pinned
source and reject stable, Alpha, edition, or provider-name collisions.

## 7. Evidence-state contract

The frozen focused tests establish candidate evidence: exact statements,
dependency-curried kernel-accepted bodies, bounded proof envelopes, recursive
empty-context closures, dependency liveness, mutation rejection, and direct
`Cut` corruption rejection. This evidence survives Git integration but does
not itself create edition membership.

The first Alpha enrollment of these rows must use:

```text
membership = alpha_only
evidence = body_checked
checked_use = false
proof_tag = null
empty_context_closure = null
```

This initial status is required even though focused tests contain concrete
closure receipts. `alpha_closed` requires a separately reviewed release batch
with repeated cold, empty-context reproduction and exact identity agreement.
No focused-test tuple may be copied into edition evidence without rerunning the
release gate against the final pushed enrollment commit.

After a qualifying batch passes Section 10, its evidence may be upgraded to
`alpha_closed` without changing theorem identity, canonical Alpha position,
origin, provenance, source, statement, dependency order, or script. Stable
promotion is a later, separately reviewed action and must use `stable_closed`
evidence in a new append-only Stable channel.

## 8. Trust and constructive-proof gates

Every row must satisfy all of the following:

1. use the unchanged ordinary intuitionistic PA checker;
2. contain zero `DNE` nodes and no classical dependency;
3. add no trusted parser, kernel, proof-reducer, arithmetic, beta, table,
   `Choose`, factorial, power, or central-binomial primitive;
4. parse as a closed formula after hygienic expansion;
5. reject generated-binder capture, invalid identifiers, invalid tags, and
   stable/Alpha/provider collisions;
6. check its dependency-curried body before any body receipt is accepted;
7. check every recursively rebuilt empty-context node against its exact
   dependency-curried target before layered compilation;
8. treat hashes and bounded-standard arithmetic only as receipts and mutation
   oracles, never proof authority; and
9. keep all source-building, tactic search, theorem selection, and layered
   compilation outside the trusted kernel boundary.

Large formula equality transports must remain scoped as in the frozen scripts.
In particular, no release rewrite may replace a term-safe local transport with
an unchecked textual substitution or teach the independent kernel to infer a
previously unsupported eliminator merely to shorten a certificate.

## 9. Mutation and dependency gates

Each row must retain the focused test's fail-closed ordering. Semantic and
kernel checks precede comparison with a non-null expected receipt. At minimum:

1. remove each direct dependency independently and require body replay to fail;
2. append a false conjunct to each theorem target and require rejection;
3. apply every frozen genuine boundary mutation and validate its explicit
   bounded-standard counterfixture;
4. reject mutations that are merely alpha-renamings, equivalent by a checked
   commutativity law, stronger-premise true theorems, or weaker conclusions;
5. corrupt every direct top-level `Cut`, including zero-`Cut` assertions for
   the two dependency-free transport rows, and require kernel rejection;
6. mutate first, middle, and terminal semantic branches where a row contains a
   multi-branch induction or table invariant;
7. preserve exact dependency order and require every local dependency to
   precede its consumer; and
8. reject authority leakage from later siblings or an unrestricted available
   theorem map.

The genuine mutations must continue to cover, as applicable:

- zero-row terminal values and row-step addition;
- predecessor-row recoding in both beta streams;
- out-of-range zero versus in-range lookup;
- different beta encodings and widths;
- diagonal and above-diagonal boundaries;
- strict-interior versus unconditional Pascal recurrence;
- complement equalities used by symmetry and weighted vertical transport;
- the exact `n + n` central carrier;
- factorial length transport and weighted multiplication association;
- successor central recurrence coefficients;
- the fourth-row seed; and
- the strict lower-bound premise and conclusion.

## 10. Capacity and cold-closure gates

No limit increase is authorized. Every body, envelope, independent row closure,
and proposed microbatch closure must remain below
`DEFAULT_LAYERED_REPLAY_LIMITS`, including:

- at most 4096 layered nodes and 65,536 dependency edges;
- at most 500,000 candidate proof occurrences;
- at most 100,000 candidate proof objects;
- proof, formula, package, and envelope depth at most 256;
- at most 5,000,000 candidate annotation occurrences; and
- the corresponding per-body and aggregate limits frozen in
  `layered_replay.py`.

At the candidate freeze, the largest row closure is
`four_pow_lt_mul_central_binom` with receipt:

```text
(412313 proof occurrences,
 157 proof depth,
 12961 proof objects,
 13309 proof edges,
 349 reused objects,
 1534101 annotation occurrences,
 162 envelope depth,
 c800194d88d778351aa13b5f9f0bbb42b9e7378a6f4699cc6294bf330c781b72)
```

This is below the current caps but close enough that retained-DAG parallelism
is forbidden on a laptop. Heavy selectors and mutation groups must run
serially in fresh processes with memory observed. A timeout does not cap
memory. If a batch approaches a cap, split proof architecture or reduce direct
dependencies before proposing a limit change.

For each of A and B, the release gate must run two independent cold
empty-context closures against the exact pushed commit. Formula identity,
topology digest, proof-DAG digest, all structural metrics, zero-`DNE` scan, and
kernel acceptance must agree. The B closure must explicitly include or consume
sealed evidence for the body-only Alpha-v7 dependency
`two_mul_eq_add_self`.

## 11. Alpha enrollment and Stable promotion sequence

The binding release sequence is:

1. preserve this RFC and the candidate freeze in local Git and the configured
   remote;
2. review the exact A and B manifests and source/test pins;
3. implement a new additive Alpha edition that preserves Alpha v7 exactly;
4. enroll the selected reviewed rows as `body_checked`, in the exact order of
   Section 5, with immutable source, test, statement, dependencies, script,
   origin, and provenance;
5. regenerate enrollment, specification, edition, membership, evidence, and
   channel roots without editing any historical artifact;
6. keep body-only lookup and replay fail-closed;
7. run both cold passes and all kernel, capacity, determinism, mutation,
   dependency-liveness, direct-`Cut`, identity, and evidence-link gates;
8. commit and push immutable cold receipts before changing evidence status;
9. upgrade only the qualifying dependency-closed rows to `alpha_closed` while
   preserving their identities; and
10. consider a keyed dependency-closed Stable subset only in a new Stable
    channel after separate promotion review.

Stable promotion is not granted by this RFC, by candidate test success, or by
Alpha enrollment. A Stable batch may contain A without B, or A together with
B, only if its complete dependency closure is independently sealed. It must
not describe the still-open Bertrand campaign as complete.

After any Alpha evidence upgrade or Stable promotion, rebuild and verify the
catalog, metrics, dependency graph, channel pointer, Book, defined edition,
Proof Explorer, Obsidian surfaces, source ledger, browser Python inventory, and
application manifest. Packaging preparation is not theorem admission, and
theorem admission is not external deployment.

## 12. Acceptance checklist

The subordinate tranche is ready for initial Alpha enrollment only when:

- [ ] the immutable Alpha-v7 parent roots match Section 2;
- [ ] all nineteen source modules and nineteen focused tests match the pinned
      commit tree;
- [ ] the exact thirty-eight names and dependency order match Section 5;
- [ ] A contains exactly 24 rows and B exactly 14 rows;
- [ ] every expanded statement and artifact identity matches its focused test;
- [ ] every dependency exists in the parent or earlier local prefix;
- [ ] every dependency-removal, false-target, genuine-boundary, capture,
      collision, and direct-`Cut` mutation fails closed;
- [ ] all bodies and envelopes pass the ordinary intuitionistic kernel with
      zero `DNE` and current caps; and
- [ ] the new edition appends rather than rewrites historical Alpha or Stable
      state.

The tranche is ready for `alpha_closed` evidence only after the two cold passes
and release gates in Sections 10 and 11. It is ready for Stable consideration
only after a separate dependency-closed promotion review. Nothing in this
document changes the parent campaign's completion criterion: BP01 and BP02
must still reach Stable, empty-context, zero-`DNE` closure with the remaining
B4--B8 mathematics and publication evidence.
