# Constructive polynomial division prerequisites for G091

This local research checkpoint contains 85 new first-order Heyting-arithmetic
theorem scripts: 26 coefficient negation/subtraction results, 22 suffix and
leading-zero trimming results, 20 monic-normalization results, and 17 modular
Horner/synthetic-division results. Their exact dependency closure contains
207 inherited Alpha-v31 theorems. Inherited support is not counted as new.

The sealed editions remain Alpha v31 (3,796) and Stable (432). The separately
checked 90-theorem G009 research tranche remains separate. None of these new
polynomial results is admitted merely by appearing in a research reader.

## Representations and exact contracts

All polynomials use the established highest-degree-first convention. A
representation consists of a beta-code pair and an explicit prefix length.
Different code pairs may have identical coefficients. Every uniqueness
statement compares decoded values, not raw code numbers.

Coefficient subtraction at index `i` witnesses actual entries `a`, `b`, `r`
and the inherited canonical operation `FpAdd(p,b,r,a)`. Negation witnesses
`FpAdd(p,a,r,0)`. Output construction, bounds, uniqueness, additive recovery,
and cancellation are theorems; they are not graph premises. Empty prefixes
are vacuous even at modulus zero. Nonempty constructive field operations
retain their explicit primality and coefficient-bound hypotheses.

Trimming witnesses `L=t+M`, an actually zero initial prefix of length `t`,
and an actual suffix code of length `M`; that suffix is empty or begins with
a nonzero decoded coefficient. A finite scan and the existing affine beta
slice constructor establish totality. No primality assumption is needed
to trim a canonical prefix. The zero polynomial has an empty trimmed
representation, not an invented natural-number degree.

Monic normalization records a genuine inverse of the actual nonzero leading
coefficient and an actual coefficientwise scalar multiplication. The output
leading coefficient equals natural field one, including characteristic two.
Monicity, preserved represented degree, and extensional uniqueness are
proved separately. No inverse of zero is asserted.

Synthetic division processes a **nonempty** input of length `S n`. An actual
modular Horner trace begins at zero and records `h[i+1]=h[i]*a+f[i]` through
the inherited field-operation graphs. An actual offset-one, stride-one
slice stores `q[i]=h[i+1]` for `i<n`; its final trace value is the remainder.
The proofs establish actual quotient/remainder construction, uniqueness of
decoded values, canonical bounds, leading and interior coefficient laws,
the final coefficient law, the exact evaluation remainder, and degree drop
for a positive-degree nonzero-leading input. Constants have an empty
quotient and their own coefficient as remainder.

## Definitions and reading surfaces

Seven conservative public graphs receive new identities ND0327–ND0333.
All 383 predecessor identities remain unchanged. The new graph reuses
`BetaPrefixInto`, `FpAdd`, `FpNeg`, `FpInv`, `FpPolyScale`, `FpHornerTrace`,
and `MatrixAffineSlice` where their actual expansions occur.

The local `polynomial-division-prerequisites` reader uses the original
Quadratic Reciprocity design and exact/defined assets. Theorem tags use
`PQ`, avoiding the existing `PD` definition namespace. Proof dependency,
theorem-uses-definition, and definition-expansion edges are distinct;
only actual proof edges determine theorem reachability and proof paths.

## Evidence gates

The final checker must authenticate the frozen source/specification and
literal complete bundle identities, replay every dependency-closed HA body,
run the pinned independently compiled Lean verifier on the same bytes,
and check six selected ordinary empty-context HA certificates. A separate
exact formula-DAG comparison tests novelty against Alpha's 3,796 statements,
the 90 G009 research statements, and all new statements in this checkpoint.

Candidate-body tests, concrete beta-code examples, hashes, saved reports,
and a successful earlier run are not substitutes for those fresh checks.
Every proof worker retains the 170/175-second CPU, 180-second wall and
1,536-MiB observed-memory gates. Explicit relevant seed bundles may be
selected for authoring, but every selected seed is checked in full.

## Explicitly open obligations

G091 remains open. This checkpoint is not general polynomial Euclidean
division by an arbitrary nonzero divisor, polynomial gcd/Bezout, an
arbitrary-convolution factor theorem, irreducible-polynomial existence in
every positive degree, or construction and exact cardinality of every
prime-power quotient field. The synthetic coefficient recurrence is a real
algorithmic step toward those results, not a reclassification of them as
already proved. The combined atlas must retain these distinctions and
preserve G009's existing research evidence and all earlier admission records.

This continuation performs no Alpha promotion, Stable change, commit,
push, deployment, public Lean-worker restart, or hosting modification.
