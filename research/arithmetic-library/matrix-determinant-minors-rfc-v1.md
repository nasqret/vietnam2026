# Constructive arbitrary signed cofactor minors and four-by-four determinants, v1

## Status, parent, and trust boundary

This RFC describes **17 dependency-ordered candidate theorems** over the
unchanged constructive Heyting-arithmetic kernel. Their parent is the immutable,
fully checked Alpha v23 edition. Each explicit tactic body is checked by the
original kernel with its declared, already checked dependencies introduced as
ordinary hypotheses. An independently closed original-kernel proof bundle and
independently compiled Lean verification are still required before any row can
obtain Alpha checked-use authority.

The source is
`peano-lab/py/peano_lab/library/matrix_determinant_minors_candidate.py`.
Original-kernel replay, dependency deletion, conclusion forgery, tactic
truncation, binder-capture, and bounded-execution adversarial tests are in
`peano-lab/py/tests/test_matrix_determinant_minors_candidate.py`.

There is no new axiom, function symbol, induction rule, sort, unrestricted
excluded middle, choice oracle, Python evaluation principle, or modified
kernel. Decidability of natural order and equality, witnessed Euclidean
division, and finite beta-prefix extension are existing constructive theorems.

## Conservative definition DAG

All four authoring relations expand immediately into first-order arithmetic.
Their binders are fresh, their parameter lists are exact, and the historical
`Lt`, `Le`, and `Beta` identities retain their existing meaning.

1. `MatrixSkipIndex(i,r,s)`:

   ```text
   (Lt(i,r) ∧ s=i) ∨ (Le(r,i) ∧ s=S(i)).
   ```

   This is the unique increasing coordinate insertion that omits the actual
   deleted row or column `r`.

2. `MatrixMinorCell(b,c,w,r,d,i,j,z)`:

   ```text
   ∃u v.
      MatrixSkipIndex(i,r,u)
    ∧ MatrixSkipIndex(j,d,v)
    ∧ Beta(b,c,u*w+v,z).
   ```

   Thus a minor entry is an actual row-major source-matrix entry, not an
   arbitrary independently supplied placeholder.

3. `MatrixMinorPrefix(b,c,w,r,d,u,v,q,l)`:

   ```text
   ∀k. Lt(k,l) →
     ∃i j z.
          k=q*i+j
        ∧ Lt(j,q)
        ∧ MatrixMinorCell(b,c,w,r,d,i,j,z)
        ∧ Beta(u,v,k,z).
   ```

   One beta code contains every exact row-major minor cell; constructive
   division exposes the row and column when the target width is nonzero.

4. `SignedMatrixMinor(pb,pc,nb,nc,w,r,d,q,up,us,un,ut)`:

   ```text
      MatrixMinorPrefix(pb,pc,w,r,d,up,us,q,q*q)
    ∧ MatrixMinorPrefix(nb,nc,w,r,d,un,ut,q,q*q).
   ```

   A signed matrix is represented by independent natural positive and
   negative component matrices. The output supplies **both** complete exact
   component codes.

The actual dependency structure is acyclic:

```text
Lt ─┐
    ├──► MatrixSkipIndex ─┐
Le ─┘                     ├──► MatrixMinorCell ─┐
                          │                     ├──► MatrixMinorPrefix
Beta ─────────────────────┴─────────────────────┘            │
                                                             ▼
                                                   SignedMatrixMinor.
```

Definition arrows indicate conservative formula expansion only; they are not
theorem-proof dependencies or extra kernel primitives.

## Exact constructive theorem layers

### Layer 1: order-preserving coordinate deletion

1. `matrix_skip_index_exists` constructively selects the correct side of the
   omitted coordinate using the existing natural-order theorem.
2. `matrix_skip_index_functional` proves that the selected source coordinate
   is independent of both witnesses.
3. `matrix_skip_index_avoids_removed` proves the mapped coordinate never
   equals the actual deleted coordinate.
4. `matrix_skip_index_bounded` proves an index below `q` maps strictly below
   `S(q)`; therefore a valid source square is never indexed out of range.

### Layer 2: exact matrix-cell and prefix construction

5. `beta_matrix_minor_cell_exists` constructs both skipped coordinates and
   the actual decoded source-matrix entry.
6. `beta_matrix_minor_cell_functional` proves the decoded value is independent
   of every skipped-coordinate witness.
7. `beta_matrix_minor_point_exists` obtains the exact row, column and entry
   of every flat target index by constructive quotient/remainder division.
8. `beta_matrix_minor_prefix_extend` appends one cell to a beta code and
   preserves every previously certified cell.
9. `beta_matrix_minor_prefix_exists_nonzero` inductively constructs every
   finite prefix when the target width is nonzero.
10. `beta_matrix_minor_prefix_empty_exists` independently handles the exact
    empty output, without any positive-dimension premise.
11. `beta_matrix_minor_prefix_exists` combines both branches and constructs
    every complete rectangular output of length `h*q`.

### Layer 3: unrestricted signed cofactor minors

12. `beta_matrix_minor_exists` proves the exact unconditional matrix-size
    theorem, including the zero-dimensional minor:

    ```text
    ∀b c q r d.
      Lt(r,S(q)) → Lt(d,S(q)) →
      ∃u v. MatrixMinorPrefix(b,c,S(q),r,d,u,v,q,q*q).
    ```

13. `beta_signed_matrix_minor_exists` proves the complete signed version with
    both actual beta-coded component outputs:

    ```text
    ∀pb pc nb nc q r d.
      Lt(r,S(q)) → Lt(d,S(q)) →
      ∃up us un ut.
        SignedMatrixMinor(pb,pc,nb,nc,S(q),r,d,q,up,us,un,ut).
    ```

Both statements quantify over unrestricted natural `q`; no Python execution
budget occurs in either formal theorem.

### Layer 4: exact genuinely signed four-by-four determinants

14. `signed_matrix_four_cofactor_expansion_exists` constructs both natural
    components of the alternating first-row Laplace expansion for four
    arbitrary signed entries and four arbitrary signed minor determinants.
15. `signed_matrix_four_cofactor_expansion_functional` proves the component
    pair is unique.
16. `signed_matrix_four_full_determinant_exists` instantiates that expansion
    with the actual recursively expanded signed three-by-three minors of all
    **32 natural components** of an arbitrary signed four-by-four matrix.
17. `signed_matrix_four_full_determinant_functional` proves both exact
    determinant components are unique.

All signed additions, products, and alternating subtractions are explicit
natural-pair expressions; no subtraction function or unbounded integer sort is
introduced. The fixed-dimensional theorem strictly extends the historical
signed two- and three-dimensional determinant results.

## Frozen authoring inventory

- Candidate theorem count: **17**.
- Direct dependency edges: **28**.
- Explicit tactic commands: **602**.
- Original-kernel dependency-curried proof nodes: **961**.
- Maximum individual proof nodes: **124**.
- Maximum individual proof depth: **82**.
- Ordered theorem-name SHA-256:
  `970a190bfb3064dce0d1caca4970fd100e98c0d26ba4f25e8766718100ca6cfe`.
- Exact natural arbitrary-dimensional minor statement SHA-256:
  `3abfa041aa3df531be6ac5580a3167802703e2adc4ecf13ae77f19309a31a8ee`.
- Exact signed arbitrary-dimensional minor statement SHA-256:
  `bf6e9238c2928e4f6525a14015198b673b41022924c6da1944ab87c8df61bba1`.
- Exact four-term signed cofactor expansion statement SHA-256:
  `f1bf20e0ba8ca02fd964b85ea1b469923bf9c9e1bb320253ebbc456fea524486`.
- Exact genuinely signed four-by-four determinant statement SHA-256:
  `7ae77d34a56bc459140fcd9afab5bb70cf4792cdb6ebac833c448381adfff848`.
- Exact signed four-by-four determinant functionality statement SHA-256:
  `d1987b1ba2337c22463858a07b85da4144d00f20f8e036c076d53d99de8ada59`.

## Explicit remaining mathematical boundary

The unrestricted **minor construction** is proved, and signed determinant
existence/functionality is proved through dimension four. However, no theorem
in this tranche constructs an unrestricted well-founded determinant-evaluation
tree or a complete encoded permutation enumeration. Consequently
arbitrary-dimensional determinants, determinant multiplicativity, rank,
Hermite/Smith normal forms, full-rank lattices and lattice reduction are **not
claimed**. The larger blueprint milestone `T13` therefore remains open.

The executable immutable minor and cofactor certificates are bounded
research aids. They independently compare first-row Laplace expansion against
the pre-existing signed permutation determinant and reject forged coordinates,
summands and sign components. They contribute no theorem or admission
authority.
