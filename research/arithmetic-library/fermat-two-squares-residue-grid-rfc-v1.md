# RFC FTS03: constructive affine square-root residue grid

**Status:** isolated dependency-curried proof candidates; no Alpha/Stable
promotion and no claim of a completed Fermat two-square theorem.

For nonzero modulus `p`, nonzero grid width `w`, root `r`, and flat index
`k`, define its grid coordinates and affine residue relationally:

```text
k = w*i + j,                    j < w,
r*i + j = p*q + t,              t < p.
```

Both quotient/remainder pairs come from the existing constructive division
theorem. The prefix relation additionally requires
`BetaAt(code,scale,k,t)` for every `k < length`; its full expansion contains
only `{0,S,+,*,=}` and existential witnesses.

The seven independently checked dependency-ordered rows are:

1. `affine_grid_point_remainder_exists`;
2. `beta_affine_residue_grid_extend`;
3. `beta_affine_residue_grid_exists`;
4. `beta_affine_residue_grid_bounded`;
5. `prime_floor_affine_residue_grid_exists`;
6. `prime_floor_affine_residue_grid_collision`;
7. `equal_affine_remainders_balanced`.

Prefix induction uses `beta_prefix_extend`; no list primitive or host
computation supplies mathematical authority. At `w = S(s)` and
`length = S(s)*S(s)`, the checked oversized-grid collision candidate then
provides actual distinct indices with equal affine residues.

Equal remainder equations imply the subtraction-free balance

```text
(r*i+j) + p*q2 = (r*i2+j2) + p*q.
```

The separate
[`collision-to-norm tranche`](fermat-two-squares-collision-norm-rfc-v1.md)
now proves that all four possible affine coordinate-difference sign patterns
yield an actual divisible two-square norm whenever `r*r + 1 = p*k`. The
subsequent
[`prime two-square theorem tranche`](fermat-two-squares-prime-rfc-v1.md)
extracts bounded nonzero differences and composes the complete constructive
prime representation. This residue-grid tranche does not claim that transport
as its own checked theorem; it belongs to the separate linked tranches. The
all-integer valuation classification and release admission remain open.

Run:

```text
cd peano-lab/py
python3 -m pytest -q tests/test_fermat_two_squares_residue_grid_candidate.py
```
