# RFC: complete signed cofactor-minor families and alternating Laplace folds

Status: candidate for additive Alpha-v25 promotion; checked in unchanged
first-order intuitionistic Heyting arithmetic against the immutable Alpha-v24
parent. The general determinant/rank/lattice milestone **T13 remains open**.

## Exact mathematical scope

For every natural `q` and every pair of beta codes for a signed square matrix of
width `S(q)`, construct one beta-coded family containing the genuine signed
first-row deletion minor for **every** column. A family entry canonically packs
all four codes/scales of that minor; decoding projects back to the checked v24
`SignedMatrixMinor` relation with removed row zero and removed column `j`.

Independently, for arbitrary natural length `l` and four signed beta-coded
source streams, construct the exact parity-adjusted term streams

```text
i even: P_i = a_i⁺d_i⁺ + a_i⁻d_i⁻, N_i = a_i⁺d_i⁻ + a_i⁻d_i⁺
i odd:  P_i = a_i⁺d_i⁻ + a_i⁻d_i⁺, N_i = a_i⁺d_i⁺ + a_i⁻d_i⁻
P = Σ_{i<l} P_i,  N = Σ_{i<l} N_i.
```

Both output components are unique independently of all beta codes, decoded
entries, term witnesses, and finite-sum traces. Finally, extract the *actual*
first row of the signed matrix and simultaneously construct its complete
genuine minor family and its alternating fold against independently supplied
signed cofactor-value streams.

The supplied cofactor values are **not yet proved to equal recursively
evaluated determinants of their associated minors**. Accordingly, this package
does not assert arbitrary-dimension determinant recursion, determinant
uniqueness, rank, or lattice closure. Concrete bounded executable cross-checks
against permutation determinants are useful examples but grant no formal proof
authority.

## Conservative definition DAG

All aliases expand to existing first-order arithmetic; no kernel symbols,
classical axioms, extraction oracles, recursive definitions, or unchecked
theorem imports are introduced.

```text
ND0058 MatrixMinorFourCode(z,up,us,un,ut)
ND0059 SignedMinorRecord(pb,pc,nb,nc,q,j,z)
       ← MatrixMinorFourCode, SignedMatrixMinor
ND0060 SignedCofactorMinorPrefix(pb,pc,nb,nc,q,b,c,l)
       ← Beta, Lt, SignedMinorRecord
ND0061 SignedAlternatingCofactorTerm(ap,an,bp,bn,i,p,n)
       ← Even, Odd
ND0062 SignedAlternatingProductPrefix(ab,ac,db,dc,eb,ec,fb,fc,ub,uc,vb,vc,l)
       ← Beta, Lt, SignedAlternatingCofactorTerm
ND0063 SignedAlternatingCofactorFold(ab,ac,db,dc,eb,ec,fb,fc,l,p,n)
       ← SignedAlternatingProductPrefix, Sum
ND0064 SignedFirstRowCofactorFold(pb,pc,nb,nc,q,eb,ec,fb,fc,p,n)
       ← MatrixAffineSlice, SignedAlternatingCofactorFold.
```

The reviewed `Sum` in `ND0063` is the checked **four-argument beta-code sum**.
Its exact blueprint alias is `BetaSum(b,c,l,z)`; the separately named generic
three-argument research `Sum(s,l,z)` remains visibly incompatible and obtains
no checked-definition authority.

## Independently checked theorem strata

1. Injective canonical four-code packing: existence, output functionality, and
   full component injectivity.
2. Genuine signed-minor records: existence and projection to the actual v24
   skipped-row/skipped-column minor relation.
3. Complete beta-coded minor families: empty prefix, extension, bounded prefix
   induction, full arbitrary-dimension family existence, individual entry
   existence, and genuine-minor projection.
4. Parity-adjusted signed cofactor terms: existence, functionality, separate
   exact even/odd equations, and existence with uniqueness.
5. Complete signed alternating product streams: empty prefix, extension,
   existence, restriction, exact decoded-term transport, and pointwise
   functionality independent of code witnesses.
6. Arbitrary finite alternating Laplace folds: existence, both-component
   functionality, existence with uniqueness, and the exact empty value.
7. Actual signed first-row extraction, arbitrary cofactor-value fold, and the
   simultaneous package containing every genuine cofactor minor.

The factory contains **29** dependency-ordered theorem bodies, **51** direct
dependencies, **1,370** checked tactics, and **2,231** original-kernel proof
nodes, with maximum proof depth **72**. Ordered theorem-name SHA-256:

```text
87a9308cecf3d377fd03c6bf51b8d28c17c334a472deec98387419e6b7055675
```

Exact major root-statement SHA-256 values:

```text
CE0009 signed_cofactor_minor_family_exists
       8486fcb74e3c32d6967e4ec4a3058c06ef7d2a6b031551e0722f73ce62b0355c
CE0017 signed_alternating_cofactor_fold_exists
       ff2d10b22ea031df2a613a9d668cdeee3c52fef7f7ab635784f68164b2a4940d
CE0019 signed_alternating_cofactor_fold_exists_unique
       cded0e0b36963f8d799d0b1a2d5a89b58ca00219d40e378bdd31cfc58addfbd5
CE001C signed_first_row_cofactor_fold_exists
       f39d7ee0acfd090d87e144b68d18ed7cb61aee9bc29dc9087c9b8f440974eb73
CE001D signed_matrix_cofactor_family_and_fold_exists
       1f013b934c7540f73e135257094d612345f43f3163b5ee7280dbe97f4f142d2a
```

## Verification and honest completion boundary

Focused tests replay every original body against immutable Alpha v24, pin
ordered names, dependency/tactic/node inventories and exact root formulas,
reject forged conclusions, truncated scripts and missing dependencies, audit
all seven hygienic expansions, and adversarially replay bounded executable
families against independent permutation determinants.

T13 can advance further only when supplied cofactor-value streams are linked
to a genuinely constructive recursively evaluated determinant for **every**
encoded minor. Rank/lattice statements additionally require their own exact
definitions, independent proofs, and promotion receipts.
