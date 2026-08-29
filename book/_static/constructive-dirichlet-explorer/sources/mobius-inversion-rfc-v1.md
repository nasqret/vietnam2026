# Full finite signed Möbius inversion

This additive research checkpoint formalizes finite Möbius inversion in the
unchanged constructive Heyting-arithmetic language. It uses independently
defined Möbius values, actual signed arithmetic tables, genuine divisor sums,
constructed convolution grids and proved finite associativity. No new axiom,
choice principle, quotient oracle, table oracle or classical rule is added.

The immutable starting inventory is Alpha v30 (3,222 checked-use theorems,
Stable 432) plus three research generations of 170, 126 and 125 theorems.
The first two research generations are published; the last 125 remain local.
Those 3,643 earlier statements are support, never counted as new results.
This checkpoint performs no admission, commit, push or remote deployment.

## Exact conservative transform graph

```text
DivisorTransform(N,F,G) :=
  ∀n z. n≠0 → Le(n,N) → ArithAt(G,n,z) → DivisorSum(F,n,z).
```

The public builder is
`signed_arithmetic_divisor_transform_relation(N,F,G,*,tag,variables)`.
Actual input-table validity is a separate hypothesis. The relation asserts
the transform at **every positive input through N**, so it is available at
every positive quotient used by convolution. It is not a single equality at
the final target input. `DivisorSum` is the previously constructed finite
mask and actual signed prefix fold, not informal summation notation.

The genuine definition dependencies are `Le`, `ArithAt` and `DivisorSum`.
The graph does not mention Möbius values or assume inversion. All bound
variables are checked against the complete declared context by the public
conservative builder; the kernel signature is unchanged.

## Principal statements

The full output-table statement is:

```text
∀N F G. ArithTable(N,F) → ArithTable(N,G) → DivisorTransform(N,F,G) →
  ∃M H. MobiusTable(N,M) ∧ DirichletTable(N,M,G,H) ∧
        ArithPositiveEqual(H,F,N).
```

`DirichletTable(N,M,G,H)` contains actual input and output table witnesses
and, at each positive index, a genuine finite signed fold of the products
`M(d)*G(q)` with witnessed `n=d*q`. Independently proved positive Möbius
values in `M` therefore make this exactly the finite weighted inversion sum.
`ArithPositiveEqual` compares represented values, not arbitrary table codes
or component encodings. All values at zero in `F`, `G` and `H` are unrestricted.
The historical Möbius-table witness retains its separate zero convention.

The stronger fixed-Möbius-table result identifies the original table itself:

```text
∀N F G M. ArithTable(N,F) → ArithTable(N,G) → MobiusTable(N,M) →
  DivisorTransform(N,F,G) → DirichletTable(N,M,G,F).
```

The full forward and reverse equivalence is also supplied:

```text
∀N F G M. ArithTable(N,F) → ArithTable(N,G) → MobiusTable(N,M) →
  (DivisorTransform(N,F,G) → DirichletTable(N,M,G,F)) ∧
  (DirichletTable(N,M,G,F) → DivisorTransform(N,F,G)).
```

No positivity condition is placed on `N`. At `N=0`, actual `M` and `H`
are still constructed and their table validity is proved; only the positive
value condition is vacuous. For positive `N`, arbitrary signed values are
allowed, including negative values represented by the existing natural-code
integer graph. Canonical signed one is code 2, not natural code 1.

## Constructive proof route

1. Construct positive constant-one and delta tables, with arbitrary chosen
   zeroth values. Prove that convolution with one is the independently defined
   actual divisor sum, and convolution with delta is the genuine identity.
2. Use the already proved prime-toggle Möbius cancellation to establish the
   actual convolution table `M*U=E`. Möbius values are not defined by this law.
3. Express the given transform as `U*F=G`, using proved commutativity.
   Constructed finite associativity identifies `M*(U*F)` with `(M*U)*F`.
   The latter is `E*F`, already proved equal to the original values.
4. Construct each actual weighted fold and prove its canonical value equals
   the original lookup. Only then is the output table legitimately chosen as
   `H=F`; the desired identity is never smuggled into its definition.
5. For the converse, use `U*(M*G)=(U*M)*G=E*G`, again with genuine finite
   folds, then recover the original divisor-transform relation.

The associativity proof constructs a real first/last-factor square grid,
identifies its rows and columns using genuine positive quotients and zero
padding, and applies the earlier actual finite Fubini theorem. Thus neither
associativity nor the required grid is an input rearrangement oracle.

## Evidence policy and campaign scope

All eight dependency-curried bodies pass the original HA checker. They have
28 declared prerequisite edges and 458 tactic commands; total body nodes are
709, maximum 216 nodes and maximum depth 46. Every body has equal occurrence
and distinct-object counts. Peak observed authoring RSS was 661,389,312 bytes.
These are conditional authoring checks, not yet a complete dependency receipt.

Before G007 is marked locally proved, every ancestor must be freshly checked
in an exact complete original-HA bundle, the same bytes must pass the unchanged
independently compiled Lean verifier, and these three principal roots must
also yield actual ordinary empty-context HA certificates:

- `mobius_inversion_for_actual_mobius_table`
- `mobius_inversion_arithmetic_tables`
- `mobius_inversion_iff`

Independent exact-AST, hygiene, dependency-mutation and actual-beta numerical
regressions are additional gates; examples and saved success sidecars never
substitute for proof checking. All 113 new campaign statements must also be
distinct from all 3,643 earlier statements and each other.

This closes the finite signed inversion goal G007 only after those gates.
G009 is broader: the arbitrary-unit inverse criterion `f(1)=+1 or -1` and
multiplicative-function closure are not proved here. General prime-power
extension fields G091 likewise remain open. The published atlas and the
Alpha/Stable membership boundaries remain unchanged by this local result.
