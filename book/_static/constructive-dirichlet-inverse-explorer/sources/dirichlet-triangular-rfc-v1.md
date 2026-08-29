# Actual triangular Dirichlet convolution: input extension

Date: 2026-08-29. This is an additive, non-admitting mathematical checkpoint
toward G009. It does not claim an inverse construction or the full G009
campaign. The previously completed G007 theorem and all 113 earlier Dirichlet
rows, their proof bundles and readers remain unchanged.

## Exact basis and scope

The basis contains 3,756 earlier statements: 3,222 Alpha-v30 statements,
170 and 126 published non-admitted research statements, and 125 and 113 local
non-admitted statements. Stable remains 432. The unchanged Alpha catalog is
`artifacts/peano-library/alpha/catalog-v30.json`, SHA-256
`ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7`.
These are genuine prerequisite specifications, not newly counted results or
an authorization to omit their complete proof checks.

The new module is
`peano-lab/py/peano_lab/library/dirichlet_triangular_candidate.py`, factory
`make_dirichlet_triangular_candidate_theorems`.
It supplies **10 statements, 43 direct prerequisite edges and 547 tactic
commands**. All relations are the exact previous definitions:

- `ArithTable(N,F)` is a genuinely packed pair of natural beta streams with
  canonical signed entries on the inclusive domain through `N`.
- `ArithAt(F,i,z)` is an actual lookup in those streams and its signed balance.
- `ArithTableEqual(F,H,l)` preserves represented values at precisely `i<l`.
- `ArithExtend(F,H,l,a)` consists of an actual output `l`-table, that prefix
  equality, and the actual new lookup `H(l)=a`.
- `DirichletPrefix(F,G,n,k,M)` is the actual inclusive summand table through
  `k`. A retained summand contains `d!=0`, an actual quotient `n=d*q`, both
  actual input lookups, and their actual signed product. Zero and nondivisors
  are masked to zero.
- `SignedPrefixSum(M,l,r)` is the actual paired natural fold at `i<l`.
  `DirichletSum(F,G,n,z)` requires `n!=0` and a real full summand prefix and
  fold of length `S n`.

No definition, alias, primitive, arithmetic oracle, kernel rule, resource
limit or previous theorem is introduced or modified. Existing conservative
definition identities and hygienic term builders are reused exactly. In
particular, no inverse equation or desired convolution value is part of a
table-validity definition.

## Restricted transport, not full-input equality

The central input-transport statement is:

```text
forall F G H n k l M.
  ArithTable(k,H) -> ArithTableEqual(F,H,l) -> k<l ->
  DirichletPrefix(F,G,n,k,M) -> DirichletPrefix(H,G,n,k,M).
```

The proof transports only the first lookup at a divisor index `d<=k<l`.
The actual quotient, second lookup and signed product are unchanged. In the
omitted branch the literal zero conclusion is retained. There is no attempt
to use the old full-prefix extensionality theorem at the newly changed index.

Consequently, `ArithExtend(F,H,l,a)` preserves each already constructed
`DirichletSum(F,G,m,z)` for `m<l`, using the same real summand and fold
witnesses. The complete earlier positive output table is preserved as well:

```text
forall N F G H K a.
  DirichletTable(N,F,G,K) -> ArithExtend(F,H,S N,a) ->
  DirichletTable(N,H,G,K).
```

The inequality is essential. Actual beta examples with the same prefix below
`l` and different entries at `l` have different convolution values at input
`l`. Preserving earlier output values does not extend the unchanged output
table to the new endpoint.

## Actual remainder and endpoint

At `n=S k`, the old first input `G` need only be an `ArithTable(k,G)`.
The existing prefix constructor takes actual zero-domain table guards; the
proved `signed_table_domain_resize` supplies these without postulating a new
value or an inverse equation. The new existence theorem constructs:

```text
forall N k F G.
  ArithTable(N,F) -> ArithTable(k,G) ->
  exists M r.
    DirichletPrefix(G,F,S k,k,M) /\ SignedPrefixSum(M,S k,r).
```

This fold includes exactly `d<S k`. It excludes the old arbitrary `G(S k)`.
Its own sum-table entry at `S k` is also unconstrained and must not be folded
into this remainder. The next theorem really recodes and appends the new
summand before constructing the longer fold.

Because beta streams are actual total natural codes, the remainder constructor
itself does not require `S k<=N`. When the surrounding inverse induction uses
only the specified positive values of `F` through `N`, that induction must
retain `S k<=N` and establish the positive quotient bounds before applying
its finite-domain assumptions. This existence lemma does not assert those
assumptions outside their domain.

For `n!=0`, the endpoint theorem proves both directions of

```text
ArithAt(F,n,a) -> ArithAt(G,1,b) ->
  (DirichletEntry(F,G,n,n,z) <-> SignedMul(a,b,z)).
```

The quotient is witnessed by the proved equation `n=n*1`; multiplication
cancellation in the inherited entry theorem identifies any alternative
quotient. The nonzero guard cannot be removed: the zeroth summand is zero,
not an arbitrary product of input zero and input one.

The main integration theorem has the following exact argument order:

```text
dirichlet_convolution_first_input_append_step:
forall k G F M r H x u y e.
  DirichletPrefix(G,F,S k,k,M) ->
  SignedPrefixSum(M,S k,r) ->
  ArithExtend(G,H,S k,x) ->
  ArithAt(F,1,u) -> SignedMul(x,u,y) -> SignedAdd(r,y,e) ->
  DirichletSum(H,F,S k,e).
```

It first proves that the old summand prefix is still a prefix for `H*F`,
then constructs the actual endpoint and the longer fold. The signed equations
are explicit premises to be solved by the separate signed-unit argument;
they are not assumed existence of a convolution or of an inverse. No unit
restriction is needed for this generic addition step.

## Input one and the zero boundaries

The second principal bridge is:

```text
dirichlet_convolution_at_one_iff:
forall F G a b z.
  ArithAt(F,1,a) -> ArithAt(G,1,b) ->
  (DirichletSum(F,G,1,z) <-> SignedMul(a,b,z)).
```

Here `<->` abbreviates the actual conjunction of the two implications. The
forward proof inspects the real two-entry fold, proves its zero prefix, and
identifies the final product. The reverse proof constructs a real singleton
zero prefix, appends the product, and constructs the fold. No premise fixes
either input's value at zero, and no global table oracle is assumed.

At `k=0`, the remainder has one actual zero entry, so its signed value is zero;
the append step constructs the convolution at input one. At an output-table
bound `N=0`, earlier positive preservation is vacuous but its table witnesses
remain actual. Scalar convolution at `n=0` remains excluded. Code `2` denotes
signed one; code `1` denotes signed minus one.

## Ordered inventory and actual body checks

Every row was replayed by the unchanged
`candidate_validation.replay_candidate_bodies`, with its exact ordered
prerequisite formulas introduced as ordinary antecedents. The final original
HA check accepted all ten conditional bodies in one fresh process:
61.757 seconds, peak resident memory 481,968,128 bytes, within unchanged
170/175 CPU seconds, 180 wall seconds and 1,536 MiB RSS.

| Theorem suffix, after `dirichlet_convolution_` | Dependencies | Commands | Body nodes/objects | Depth |
| --- | ---: | ---: | ---: | ---: |
| `entry_first_input_transport` | 2 | 48 | 134 | 72 |
| `prefix_first_input_transport` | 2 | 41 | 98 | 49 |
| `first_input_append_preserves` | 2 | 36 | 102 | 58 |
| `table_first_input_append_preserves` | 3 | 46 | 127 | 58 |
| `last_entry_iff` | 3 | 42 | 105 | 37 |
| `strict_prefix_exists` | 3 | 36 | 42 | 17 |
| `prefix_last_step` | 6 | 83 | 114 | 45 |
| `first_input_append_step` | 4 | 50 | 139 | 78 |
| `zero_prefix_sum` | 5 | 40 | 77 | 27 |
| `at_one_iff` | 13 | 125 | 269 | 43 |
| Total | 43 | 547 | 1,207 | maximum 78 |

All 1,207 body occurrences are distinct proof objects in their respective
bodies. Source SHA-256:
`5b6e585a4b2df25dee069ddec17e26cddc52c329d45ee7c5fcf307314b10f8ef`.
Complete ordered-specification SHA-256:
`a91a79108e1a636bfdd78a67e3426d33edb2e493be1d43f379aef367db743733`.
Ordered names joined by newlines without a trailing newline:
`a94e7a4b3092b11afbfe54f8aa358f6065bcd34e1164c4f1094d52976f7cb010`.

Recommended three principal statements and their exact SHA-256 values:

- `dirichlet_convolution_first_input_append_step`:
  `0acd77c052775df9717c6c09715c733ab207c9fa18380b5e279222221a5f1404`.
- `dirichlet_convolution_at_one_iff`:
  `6f1888f04b4d2ac46a57cca07719bed191aa2c1e3fc6092ef671965cc8d6b956`.
- `dirichlet_convolution_strict_prefix_exists`:
  `745ac62f2fbed061d5ba9f77972361c063ec4020ed9e52144bd2a1b8a38b96d1`.

The focused tests independently expand every target, exercise compound and
repeated terms, check the exact 3,756-row AST novelty boundary, and construct
actual paired beta streams and natural cumulative traces. Hostile cases alter
strictness, endpoint, fold length, quotient lookup, signed product, addition
and input extension, as well as every declared dependency. The numerical
examples include arbitrary input-zero values, negative values, distinct
component representations, `k=0` and large integers. They are diagnostics,
not mathematical proof authority.
A rejected changed target means the original body does not establish that
target; only the explicit numerical counterexamples disprove the particular
false boundary strengthenings they exercise.

The final focused suite passed **220 distinct tests** in seven disjoint fresh
windows. Repeated authoring diagnostics are not counted again:

| Window | Tests | Pytest seconds | Peak RSS bytes |
| --- | ---: | ---: | ---: |
| Independent contracts, contexts, novelty and actual beta models | 89 | 51.46 | 443,318,272 |
| All actual bodies, false targets and absent bodies | 30 | 60.02 | 533,774,336 |
| Dependency removal, first 22 | 22 | 37.58 | 488,914,944 |
| Dependency removal, remaining 21 | 21 | 91.17 | 483,393,536 |
| Dependency poisoning, first 22 | 22 | 37.89 | 408,338,432 |
| Dependency poisoning, remaining 21 | 21 | 92.75 | 478,445,568 |
| Altered bounds, endpoint, product, addition and extension | 15 | 39.53 | 450,936,832 |
| Total distinct cases | 220 | 410.40 across separate windows | maximum 533,774,336 |

The maximum successful process window was 92.864 seconds. Each process kept
the original 170/175 CPU-second, 180 wall-second and 1,536 MiB RSS bounds;
the sum of separate windows is not a larger proof allowance. No case was
skipped and no resource or proof limit changed.

The new test file offers explicit bounded selections. With
`PYTHONPATH=peano-lab/py:scripts` and `PYTHONMALLOC=malloc`, invoke
`python3 -u peano-lab/py/tests/test_dirichlet_triangular_candidate.py` with:

- `--pytest-select 'not original_kernel_body and not false_target and not missing_body and not dropped_dependency and not poisoned_dependency and not changed_domain'`;
- `--pytest-select 'original_kernel_body or false_target or missing_body'`;
- `--pytest-select dropped_dependency --case-start 0 --case-count 22`, then
  the same selector with `--case-start 22 --case-count 21`;
- `--pytest-select poisoned_dependency` with the same two explicit ranges;
- `--pytest-select changed_domain`.

The selected ranges exhaust the 220 collected cases; deselection only divides
them into separate bounded processes. A single body can also be replayed with
`--body THEOREM_NAME` under the same limits.

## Evidence boundary and next proof

The present authoring evidence proves the exact dependency-curried bodies.
It is not a complete empty-context replay, independently compiled Lean receipt,
edition enrollment or publication. The main integration must close and check
every actual inherited prerequisite and every owned body. Digests identify
inputs and never replace those checks.

To complete the inverse criterion, the next layer must actually solve the
signed linear equation when `F(1)` is signed plus or minus one, construct
the inverse by prefix induction, and handle `N=0` separately. Necessity uses
the at-one bridge followed by a proved classification of signed factors of
one. General multiplicative-function closure remains another G009 obligation.
These tasks are not conclusions of the ten lemmas here.

No old mathematical source, definition record, kernel or engine module,
artifact, explorer, global plan, worker, Makefile or remote state was modified
by this three-file checkpoint. The constructive-proof-explorer skill kept
the definitions conservative and the conditional/full-proof/admission
boundaries separate; no website regeneration or publication was performed.
