# Exact nondegenerate square-matrix data and the full-rank interface

Status: all 23 additive original-kernel candidate bodies are implemented and
individually checked. This is a body-authoring RFC, not a full closure, Lean,
or Alpha admission receipt. It extends the frozen determinant, rank, and
integer-representation-invariance candidates without modifying them.

## Blueprint boundary

The blueprint's opaque `Lattice(B,d,D)` planning notation requires a
positive dimension, an integral square matrix, and `D=|det B|>0`. Closure of
an arbitrary column span alone does not establish these conditions.

The explicit beta-code realization introduced here is
`PositiveDeterminantMatrixData(ab,ac,bb,bc,d,D)`, meaning:

`d ≠ 0 ∧ D ≠ 0 ∧ ∃p n. ActualDeterminant(ab,ac,bb,bc,d,p,n) ∧`
`(p=n+D ∨ n=p+D)`.

The four code parameters give the actual positive and negative component
entries of a `d × d` integral matrix. The absolute determinant is genuinely
computed from the unrestricted recursive determinant relation. Neither `D`
nor the determinant is an arbitrary supplied label.

This is **matrix data**, also suitable as the blueprint's positive absolute
determinant/covolume-data field. It is not a theorem identifying a geometric
covolume, subgroup index, or fundamental-domain volume. No injectivity of
the integer column map, independent lattice basis, Smith/Hermite normal
form, Cramer rule, or LLL theorem is claimed.

## Proved endpoints

- Every square matrix, including dimension zero and singular matrices, has
  exactly one actual natural absolute determinant.
- A positive-dimensional square matrix with an actually nonzero full
  determinant has a constructively obtained unique positive absolute-
  determinant data value.
- Absolute determinant and positive determinant data transport across
  arbitrary entrywise integer-equal signed-pair representations.
- A genuinely nonzero full determinant implies actual full determinantal
  rank `d`, including the `d=0` boundary.
- Positive absolute-determinant matrix data therefore entails full rank.

The main construction theorem assumes only `d ≠ 0`, an actual determinant
evaluation, and `p ≠ n`. It does not assume the data it constructs. The
full-rank theorem does not need a positive-dimension premise: the empty
determinant `(1,0)` supplies the exact zero-order witness.

## Construction and definition DAG

`AbsoluteRecursiveDeterminant` sits above the actual determinant relation
and the ordinary natural gap disjunction `p=n+D ∨ n=p+D`.
`PositiveDeterminantMatrixData` adds the two required strict positivity
conditions. All are hygienic conservative formulas in unchanged HA.

Natural order constructs the absolute difference. Cancellative arithmetic
proves that opposite nonnegative gaps must both vanish, giving uniqueness
including zero. Cross-sum integer equality transports the actual gap, so the
absolute determinant is representative-independent.

`IdentityMatrixSelector(b,c,d)` is a real beta prefix with entry `i` at every
index `i<d`. The checked range construction produces it, and beta uniqueness
proves its injectivity. Actual quotient/remainder coordinates show that
selecting every row and column with this prefix gives exactly the original
matrix codes. Thus a nonzero full determinant provides a genuine nonzero
full-order minor. Constructive finite pigeonhole excludes all higher-order
selectors, proving full rank without assuming a basis theorem.

## Exact inventory and checks

Factory: `make_matrix_lattice_data_candidate_theorems`.

There are 23 rows, 52 direct declared dependencies, and 816 tactic commands.
Their actual bodies contain 1,456 node occurrences and 1,455 distinct proof
objects; the opposite-gaps-zero body shares one object. The largest body has
136 nodes; greatest actual body depth is 46. The complete 23-body diagnostic
stayed below 225 MiB measured peak RSS. These counts exclude historical
dependency bodies and are not release-bundle counts.

Ordered-name SHA-256:
`18f9162bf5b71d117c798edb2ac391cdd8021486690208fc91a489233ea4c54f`.

Principal statement SHA-256 pins:

- `absolute_recursive_determinant_exists_unique`:
  `1a01953c2267c95c0c92fb0b853dade02a33fbf1dbee71af3dfa3a97378bcad8`;
- `positive_determinant_matrix_data_exists_unique`:
  `2d8c3aec5c5751dc8325a28477c9b6c7b7ddd8d8cd20bcc719d7af518bcc2676`;
- `positive_determinant_matrix_data_full_rank`:
  `2d861924f0f0b78f626e57e1521a2fa6145abe7bf1eadae069ecd2a906b20b48`.

Tests pin exact body structure and statement boundaries, both data positivity
conditions, actual absolute-value orientation, unrestricted full-rank
dimension, source/dependency inventory, inherited binder hygiene, and
false-conclusion/missing-dependency rejection. Original-kernel body checking
is not substituted for the separate full dependency reconstruction and
independent Lean release checks.
