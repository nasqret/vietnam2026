# Fermat's prime two-square theorem: constructive kernel-checked candidate

The isolated final-assembly factory contains **nine independently
kernel-checked first-order HA theorem bodies** and proves the exact flagship

```
prime_mod_four_one_is_sum_of_two_squares:
  forall p n.
    p = S n ->
    Prime(p) ->
    (exists t. p = 4*t+1) ->
    exists x y. p = x*x+y*y.
```

`Prime`, inequalities, floor square root, beta coding, divisibility, and
balanced congruence are all expanded into the unchanged language
`{0,S,+,*,=}`. Both coordinates are existentially witnessed natural numbers;
the proof uses neither classical excluded middle nor double-negation
elimination.

The canonical first supplementary law supplies a witnessed root
`r*r+1 = p*q`. Constructive floor-square totality chooses `s`; the already
proved beta-coded affine map on `(s+1)^2` points gives two distinct indices
with the same residue. Beta uniqueness identifies the decoded remainders,
and their affine values are proved congruent modulo `p`.

Natural absolute coordinate differences handle all four sign cases. Both
decoded rows and columns lie below `S s`, so both differences are at most
`s`. Distinct flat indices prove the differences cannot both vanish; their
two-square norm is therefore strictly positive. The established collision
transport produces a witnessed multiple of `p`, and the existing bounded
norm theorem identifies that multiple exactly with `p`.

The flagship statement SHA-256 is
`41ee377098bb3cc2156a1c8c5ff724d4c2bdbbd72eafa64edd141011291e5ee4`.
Its exact dependencies are:

1. `prime_mod_four_one_bounded_divisible_two_square_norm_exists`.
2. `floor_sqrt_total`.
3. `prime_floor_affine_residue_grid_collision`.
4. `prime_floor_affine_grid_collision_represents_prime`.

The final dependency-curried body has **45 commands, 61 proof nodes, and
proof depth 27**. Across all nine rows the maximum is **146 nodes** and
depth **47**. Focused tests pin names, statements, dependencies, body
receipts, reject an intentionally false flagship mutation, and check small
prime examples.

This is a complete mathematical proof **at the isolated candidate-body
layer**. It is not yet enrolled in the public theorem registry, admitted
into an alpha release, promoted to stable, or published in a proof explorer;
those remain separate release and presentation operations.
