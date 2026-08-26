# Constructive coded matrix multiplication and signed foundations, v1

## Status and trust boundary

This document describes 23 dependency-ordered **candidate** theorems, not an
admission receipt. Every tactic body is checked by the unchanged
Heyting-arithmetic kernel with its explicitly declared, previously checked
dependencies introduced as ordinary hypotheses. An independently closed
release bundle is still required before any candidate obtains checked-use
authority.

The immutable parent is Alpha v20. No new axiom, sort, function symbol,
general excluded-middle principle, choice oracle, Python evaluation rule, or
kernel modification participates in these proofs. Natural-number equality is
constructively decidable, and the existing beta-prefix extension and
Euclidean division theorems provide all finite witnesses.

The implementation is
`peano-lab/py/peano_lab/library/matrix_coded_product_candidate.py`; its
independent kernel, hygiene and mutation tests are in
`peano-lab/py/tests/test_matrix_coded_product_candidate.py`.

## Conservatively shared definition DAG

Every display name below is an authoring abbreviation for an expanded
first-order formula over `0`, successor, addition and multiplication. Its
source helper validates every free argument and binder tag before expansion.

1. `Beta(b,c,i,a)` is the existing four-argument beta decoding relation.
2. `AffineMatrixSlice(b,c,s,d,u,v,l)` means that, at every `i < l`, the
   decoded target entry `Beta(u,v,i,z)` equals the source entry
   `Beta(b,c,s+d*i,a)`.
3. A row slice uses `s=i*w` and `d=1`; a column slice uses `s=j` and
   `d=v`. Consequently left entries are read at `i*w+k`, and right entries
   at `j+v*k`, constructively equal to the customary `k*v+j`.
4. `MatrixProductCell(lb,lc,rb,rc,w,v,i,j,n)` existentially packages the
   actual coded row, coded column and already checked natural
   `DotProduct(row,column,w,n)`.
5. `MatrixProductPrefix(lb,lc,rb,rc,w,v,tb,tc,l)` witnesses, for every
   `k < l`, genuine `i,j,n` with `k=v*i+j`, `j<v`, the exact product cell,
   and `Beta(tb,tc,k,n)`.
6. `PointwiseAdd(mb,mc,sb,sc,tb,tc,l)` says every bounded decoded target
   entry is exactly the sum of its two corresponding decoded source entries.
7. `SignedDot(lp,lps,ln,lns,rp,rps,rn,rns,l,p,n)` packages all four natural
   dot products and sets `p=dot(lp,rp)+dot(ln,rn)` and
   `n=dot(lp,rn)+dot(ln,rp)`.
8. `SignedMatrixProduct(lp,lps,ln,lns,rp,rps,rn,rns,w,v,r,p,ps,n,ns)`
   packages four complete natural matrix products of length `r*v` and two
   exact `PointwiseAdd` codes. The final beta codes represent

   ```text
   positive = LP·RP + LN·RN
   negative = LP·RN + LN·RP.
   ```

Thus the named definition dependencies form the acyclic chain

```text
Beta ─┬─► AffineMatrixSlice ─► MatrixRow / MatrixColumn ─┐
      ├─► DotProduct ────────────────────────────────────┼─► MatrixProductCell
      ├─► Euclidean quotient/remainder ──────────────────┘         │
      ├─► PointwiseAdd ◄───────────────────────────────────────────┤
      │                                                            ▼
      │                                      MatrixProductPrefix ─► MatrixProduct
      │                                                            │
      └─► SignedPair ─► SignedDot / SignedDet2 / SignedDet3        ▼
                                                      SignedMatrixProduct.
```

There is no cyclic alias and no argument-arity conflation. In particular,
`MatrixProductPrefix` and `SignedMatrixProduct` are distinct relations with
nine and fifteen arguments respectively; a signed result is **two complete
beta-coded output matrices**, not a claim that four intermediate streams are
already a signed output.

## Exact proof layers

### Layer 1: affine row and column recoding

1. `beta_affine_matrix_slice_extend` appends the next actual decoded source
   value and proves preservation of every earlier decoded target value.
2. `beta_affine_matrix_slice_exists` inductively constructs the complete
   finite affine slice.
3. `beta_matrix_row_slice_exists` specializes to row-major stride one.
4. `beta_matrix_column_slice_exists` specializes to column stride equal to the
   declared matrix width.

### Layer 2: arbitrary natural matrix multiplication

5. `beta_matrix_product_cell_exists` constructs the row, column and exact dot
   product for each requested coordinate.
6. `beta_matrix_product_point_exists` constructively divides the flat output
   index by a nonzero output width and computes its exact cell.
7. `beta_matrix_product_prefix_extend` appends that cell and preserves every
   earlier row, column, value and beta witness.
8. `beta_matrix_product_prefix_exists_nonzero` inductively codes every finite
   prefix when the output width is nonzero.
9. `beta_matrix_product_exists_nonzero_width` specializes to the complete
   output length `rows*output_width`.
10. `beta_matrix_product_empty_exists` handles empty output independently of
    all dimension assumptions.
11. `beta_matrix_product_exists` uses constructive decidability of natural
    equality to cover nonzero and zero output widths. It proves the actual
    unconditional arbitrary finite **natural** matrix product theorem.

### Layer 3: complete arbitrary signed matrix multiplication

12. `beta_pointwise_add_prefix_extend` appends one exact natural component sum.
13. `beta_pointwise_add_prefix_exists` inductively codes all component sums.
14. `beta_signed_matrix_product_exists` invokes the full natural matrix result
    four times, combines the intermediate codes by the two pointwise-add
    theorems and returns both complete signed output beta codes. All row,
    inner-width and output-width boundaries, including zero, are covered.

The precise root statement is the fully expanded HA form of

```text
∀LP LPscale LN LNscale RP RPscale RN RNscale w v r.
  ∃P Pscale N Nscale.
    SignedMatrixProduct(LP,LPscale,LN,LNscale,
                        RP,RPscale,RN,RNscale,
                        w,v,r,P,Pscale,N,Nscale).
```

Its statement SHA-256 is
`13291ba49b84a8b1345863e446bca126321e7962eb912bd84b48761f9db24c7f`.

### Layer 4: signed vectors and fixed-dimensional determinants

15–16. `signed_pair_product_exists` and `signed_pair_product_functional`
construct and uniquely determine the two natural components of signed scalar
multiplication.

17–19. `beta_signed_dot_product_exists`,
`beta_signed_dot_product_functional`, and
`beta_signed_dot_product_exists_unique` construct and uniquely determine both
components of an arbitrary finite signed-vector dot product.

20–21. `signed_matrix_two_full_determinant_exists` and
`signed_matrix_two_full_determinant_functional` handle all eight natural
components of a genuinely signed two-by-two matrix; this is stronger than
the historical theorem for a matrix with natural entries only.

22–23. `signed_matrix_three_full_determinant_exists` and
`signed_matrix_three_full_determinant_functional` give the exact constructive
cofactor expansion for all eighteen natural components of a genuinely signed
three-by-three matrix.

## Pinned authoring inventory

- Theorem count: **23**.
- Dependency edges: **41**.
- Tactic commands: **998**.
- Independently kernel-checked dependency-curried proof nodes: **1,298**.
- Ordered theorem-name SHA-256:
  `21012fdc098513a9d0f5ca9bd57a31afd8f69d174c4df32639b4f2cf3a3814c3`.
- Unconditional natural matrix multiplication statement SHA-256:
  `c2d3335be60c889559096aa9a36ed8d9bd38c8b33b5f776d73cdec0a60e951c2`.
- Complete signed matrix multiplication statement SHA-256:
  `13291ba49b84a8b1345863e446bca126321e7962eb912bd84b48761f9db24c7f`.
- Exact signed-vector existence/uniqueness statement SHA-256:
  `f84fbb5d723d32ea972a38d562c3e59cbedc78ab485e9f20cda90c0c4f186c04`.
- Exact signed three-by-three determinant statement SHA-256:
  `edd7918f03a700f96dc345ba77e3dae458485fb323162139c2e93dbc09fae784`.

## What remains genuinely open

The T13 campaign milestone is **not** closed by these results. Its arbitrary
signed matrix multiplication prerequisite is now proved, but no claim is made
for arbitrary-dimensional determinant coding, determinant multiplicativity,
rank, Hermite/Smith normal forms, full-rank lattices, lattice covolume,
positive-definite Gram matrices or LLL reduction. The executable certificate
dimension budgets are defensive Python limits only; the formal theorem
statements themselves quantify over unrestricted natural dimensions.
