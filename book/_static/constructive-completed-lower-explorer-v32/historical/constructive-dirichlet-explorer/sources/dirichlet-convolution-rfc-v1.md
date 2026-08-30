# Actual finite Dirichlet convolution

This additive module constructs Dirichlet convolution from actual finite
signed tables. Its 30 statements are distinct from all 3,643 earlier
statements: Alpha v30's 3,222 theorems, the two published non-admitted
research generations of 170 and 126, and the local continuation's 125.
No inherited source, artifact, definition, kernel rule or resource limit is
changed. This core is a prerequisite for G007 and G009, not an assertion
that either entire milestone follows from these 30 statements alone.

## Independent relations and domains

The following are abbreviations for ordinary first-order arithmetic, not
additional function symbols or axioms. `ArithAt` returns a canonical signed
code from the historic nested packing of two natural beta streams;
`SignedMultiply` is the existing signed-integer graph.

```text
DirichletEntry(F,G,n,d,z) :=
  (d != 0 /\ exists q a b.
     n=d*q /\ ArithAt(F,d,a) /\ ArithAt(G,q,b) /\ SignedMultiply(a,b,z))
  \/ ((d=0 \/ ~Dvd(d,n)) /\ z=0).

DirichletPrefix(F,G,n,l,M) :=
  ArithTable(l,M) /\ forall d z.
    Le(d,l) -> ArithAt(M,d,z) -> DirichletEntry(F,G,n,d,z).

DirichletSum(F,G,n,z) :=
  n != 0 /\ exists M.
    DirichletPrefix(F,G,n,n,M) /\ SignedPrefixSum(M,S n,z).

DirichletTable(N,F,G,H) :=
  ArithTable(N,F) /\ ArithTable(N,G) /\ ArithTable(N,H) /\
  forall n z. n != 0 -> Le(n,N) -> ArithAt(H,n,z) -> DirichletSum(F,G,n,z).
```

`Dvd(d,n)` itself supplies a real natural quotient. The retained entry
contains the particular equation `n=d*q`; no quotient lookup or oracle is
assumed. The summand at zero is always zero regardless of `F(0)` and `G(0)`.
Nondivisors are likewise masked. The final fold has **S n entries**, indexed
0 through n; its last entry generally contributes `F(n)*G(1)` and cannot
be dropped.

Finite prefixes are constructible for every n and every independent length
l, including n=0. At n=0 a finite prefix can use `G(0)` at positive divisor
indices; this does not define a Dirichlet sum at zero. The scalar sum graph
explicitly excludes zero. At N=0 the output-table graph still has genuine
input and output table witnesses, but its positive-window specification is
vacuous and imposes no value on `H(0)`.

The four public relation builders are
`dirichlet_convolution_entry_relation(F,G,n,d,z)`,
`dirichlet_convolution_prefix_relation(F,G,n,l,M)`,
`dirichlet_convolution_sum_relation(F,G,n,z)` and
`dirichlet_convolution_table_relation(N,F,G,H)`, each with explicit keyword
arguments `tag` and `variables`. Compound arithmetic terms are parsed in the
entire supplied context. Every generated nested binder is checked against
that context; unrelated context variables cannot be captured silently.

## Constructive proof route

The seven entry lemmas construct and identify the actual product-or-zero
entry. Divisibility is decided for a nonzero divisor, its quotient witness is
extracted, both signed values are genuinely decoded, and their signed
product is constructed. Nonzero multiplication cancellation identifies any
two supplied quotient witnesses.

The eight prefix lemmas start with an actual singleton zero table and use
the already proved paired-beta append construction. Ordinary induction on
l constructs the entire prefix, preserving all preceding represented
values. Prefixes can then be restricted, queried at a witnessed quotient,
or queried at an omitted index. Functionality compares signed values, not
raw component streams or packed table codes.

Four scalar-sum lemmas construct the original finite positive/negative
folds, prove their canonical signed value unique and exclude n=0. Four
source-transport lemmas show that, for positive n, the actual quotient is
positive and at most n before positive-window source equality is used.
All four compared zeroth input values may remain unrelated.

Seven output-table lemmas iterate the genuine scalar construction and
append. In particular:

```text
forall N F G n.
  ArithTable(N,F) -> ArithTable(N,G) -> n!=0 -> Le(n,N) ->
  exists z. DirichletSum(F,G,n,z) /\
    forall w. DirichletSum(F,G,n,w) -> w=z.

forall N F G.
  ArithTable(N,F) -> ArithTable(N,G) ->
  exists H. DirichletTable(N,F,G,H) /\
    forall K. DirichletTable(N,F,G,K) -> ArithPositiveEqual(H,K,N).
```

`ArithPositiveEqual` compares exactly 0<i<=N. Neither theorem asserts
uniqueness of a beta encoding, positive/negative representatives, or the
output's unconstrained zeroth value. Append preserves that chosen zeroth
value, and restriction works down to bound zero.

## Companion commutativity and padding component

The local `dirichlet-convolution` checkpoint groups this 30-row core with
the ten separately authored rows in `dirichlet_commutativity_candidate.py`:
40 new theorems, 102 direct prerequisite edges and 1,754 tactic commands.
Its additional proof route and 114 focused-test results are recorded in
[Complementary-divisor reindexing for actual convolution](dirichlet-commutativity-rfc-v1.md).
Those rows construct and use the actual complementary-divisor permutation,
prove scalar and whole-table commutativity, and identify longer zero-padded
prefix folds with the original convolution value. They introduce no new
relation and do not count the 30 core rows again as independent discoveries.
The component metrics and 372 tests below refer specifically to the core;
the complete 40-row checkpoint still needs the separate full-closure gates.

## Evidence, tests and unchanged limits

All 30 dependency-curried bodies pass
`candidate_validation.replay_candidate_bodies`, including its unchanged
original-kernel final check. There are 68 direct prerequisite edges and
1,273 primitive tactic commands. The bodies contain 2,461 proof-node
occurrences and 2,460 distinct proof objects in total. The largest body has
333 occurrences and 332 objects; maximum depth is 64. Reused proof objects
are not counted as distinct objects.

All 372 distinct focused tests pass in fresh bounded windows. They include
independent exact ASTs for every statement and all four public graphs,
compound and 96-bit numeral arguments, full nested-binder collision checks,
all 68 dropped dependencies and all 68 poisoned dependency statements,
false targets, missing bodies, unproved guard-removal/stronger-uniqueness
mutations, and exact AST novelty against all 3,643 prior statements.
Numerical diagnostics build actual nested beta codes, both component
prefix-sum traces, prime/composite masks and alternative representations.
They cover n=1, N=0, n distinct from prefix length, arbitrary input/output
zero values, genuine quotient bounds and the essential final divisor.
These numerical examples are not universal proof evidence.

The longest observed focused-test window took 89.96 seconds. Across the
focused windows, peak RSS was 446,627,840 bytes. A separate complete 30-body
metrics replay took 52.72 seconds and peaked at 430,178,304 bytes; the final
30-body regression with exact metric pins passed in 53.82 seconds. All windows retain the original
170/175 CPU-second, 180 wall-second and 1,536 MiB bounds.

Reproducible bounded groups, with `PYTHONPATH=peano-lab/py`, use the new test
file's `--pytest-select` switch:

```text
original_kernel
not original_kernel and not dropped_dependency and not poisoned_dependency
  and not false_target and not missing_actual_body and not novelty
  and not unproved_guard
dropped_dependency or false_target or missing_actual_body
poisoned_dependency or unproved_guard or novelty
```

The frozen mathematical source SHA-256 is
`cec111fbad76f106a5a3f79e2d78fc2a8d483267baa1b19738d4cbfb0c0fb342`;
the ordered specification digest is
`1c87a5bb73650525068f27c1034b2b1ed97ca0023877d23e334c73f925cdce36`.
Those hashes identify source and syntax, not proof authority. Complete
dependency closure, fresh compiled-Lean verification and ordinary
empty-context principal certificates are separate required integration
gates. This RFC records body checking only. It claims no Alpha/Stable
admission, publication, commit or deployment, and does not by itself close
Möbius inversion, general Dirichlet inverses or multiplicative-function laws.
