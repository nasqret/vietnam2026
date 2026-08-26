# Alpha v24: constructive matrix, polynomial, and CRT research foundations

Status: additive, independently original-kernel-checked and compiled-Lean-
verified research release. The immutable Stable edition is unchanged.

## Immutable checked parent

Alpha v23 contains exactly **1,949 independently checked-use theorems**,
including exactly **432 unchanged Stable theorems**. Its exact enrollment
identity is
`f5d94af7a11c642d7076a195e2e795e7b84c61a6de1a6b074708669b2dac1648`, its edition
identity is
`02059eef420eb96abd48c41bf62049a3cc69f025b00bed9dc3466e7eb2294a85`, and its
catalog SHA-256 is
`818da349674b1ef33c17fa85b2e9a0a6653370046d88e7814300297f7bc7f4d2`.

Every historical statement, checked proof body, source binding, immutable
release artifact, Stable pointer, logical signature, induction rule, and
intuitionistic kernel is preserved without modification.

## Exactly three additive constructive research campaigns

1. **Arbitrary matrix cofactor minors and four-dimensional determinants:**
   **17 checked theorems**, **28 direct dependencies**, and **602 authored
   tactic commands** construct exact arbitrary-dimensional row-major natural
   and signed cofactor minors, with arbitrary deleted row and column. They
   additionally prove existence and functionality of the fully signed 4×4
   determinant. Arbitrary-dimensional determinants, rank, and lattices are
   not proved: the full T13 matrix/lattice milestone remains **open**.
2. **Exact formal polynomial derivatives:** **15 checked theorems**, **27
   direct dependencies**, and **583 authored tactic commands** construct
   coupled beta-coded Horner traces. The exact successor rules are
   `value' = value*t + coefficient` and
   `derivative' = derivative*t + value`; both output components exist
   uniquely for every finite coded polynomial. Constant and linear boundary
   cases are independently proved. Taylor divisibility, modular-inverse root
   correction, and full simple-root Hensel lifting are not proved: G095 remains
   **open**.
3. **Finite Chinese remainder and arbitrary-list LCM:** **27 checked
   theorems**, **83 direct dependencies**, and **1,106 authored tactic
   commands** construct the unique universal-property LCM for every finite
   beta-coded list, including non-coprime and zero modulus entries. They prove
   exact solution-class classification and the complete bounded canonical CRT
   solution for every arbitrary finite list of positive pairwise-coprime
   moduli. The compatibility-to-accumulated-LCM bridge for arbitrary
   non-coprime lists is not proved: the unrestricted G011 milestone remains
   **open**.

The additive release contains **59 new theorems**, **2,008 checked-use
theorems**, **1,576 Alpha-only theorems**, **432 Stable theorems**, **6,423
direct proof-dependency edges**, and **53 dependency-first layers**. The new
theorem rows contain **138 direct dependency edges** and their ordered-name
SHA-256 is
`e88ec1f9a1242c339565305bd7a866a0ec1e95a069f537af1712abf364433947`.
The exact Alpha-v24 enrollment identity is
`7463b938ffb87fe85eea6cd0e40c10ac73c799087ca1c408a070fcbe2687d4e1`;
the exact edition identity is
`1f4390b8ca5784ece54857fa666007f884b79e2670ef8bb32b2710c10f298a1b`.

## Complete dependency-closed proof certificate

The genuine cone contains **202 actual theorem proof bodies**, **18 maximal
checked theorem endpoints**, and one unenrolled synthetic packaging root.
Its compact artifact contains **203 independently kernel-checked nodes**,
**502 actual dependency edges**, **11,065 structural body-proof nodes**, and
exactly **738,923 bytes**. Its SHA-256 is
`627e39ed29b10db48bf37d5bef8750d48009a7524c822a7c5e7c83e96a8e9cf9`.

Exactly **59 new proofs** and **14 genuinely needed historical parent proofs**
are reconstructed in bounded one-theorem microbatches. Frozen independently
checked bodies are reused from Alpha-v19 residual closure (**2**), Alpha-v19
frontier (**3**), Alpha v20 (**1**), Alpha v21 (**115**), Alpha v22 (**5**),
and Alpha v23 (**3**). No historical body, synthetic conjunction, Python
example, cached hash, or external calculation is counted as a new theorem.

The unchanged Heyting-arithmetic kernel accepts every one of the **203**
ordinary proof nodes. A separately compiled Lean verifier independently
returns `ACCEPT ... nodes=203 root=202` for precisely the same artifact.

## Hygienic conservative definition sharing

The twelve newly reviewed definitions have stable identities `ND0046` through
`ND0057`: `MatrixSkipIndex`, `MatrixMinorCell`, `MatrixMinorPrefix`,
`SignedMatrixMinor`, `HornerDerivativeTrace`, `HornerDerivative`,
`HornerDerivativeOnly`, `CRTPositiveModuliPrefix`,
`CRTPairwiseCoprimePrefix`, `CRTPrefixSolution`, `CRTPrefixLCM`, and
`CRTCanonicalPrefixSolution`.

The global registry contains **164 blueprint definitions**, **109 hygienic
independently reviewed conservative definitions**, **186 reviewed-definition
dependency edges**, and **73 compatible blueprint/registry identities**:
**69 exact-name matches** and **four explicitly reviewed aliases**. The two
historically incompatible signatures remain explicitly classified. Definition
sharing does not create theorem proofs, new function symbols, axioms, or
logical principles.

No excluded middle, Markov principle, unbounded choice, reflection axiom,
unverified solver result, external arithmetic oracle, or new sort is added.
