# Fermat two-square affine collision-to-norm transport, v1

This isolated first-order HA tranche contains **15 independently
kernel-checked constructive theorem candidates**. It changes neither the
public registry nor any alpha/stable release edition.

## Checked constructive bridge

Balanced congruence is expanded as

`ModEq(p,u,v) := exists m n. u + p*m = v + p*n`.

The principal proved endpoint is

```
affine_collision_absolute_difference_norm_multiple:
  forall p r a b c d.
    (exists k. r*r+1 = p*k) ->
    ModEq(p, r*a+b, r*c+d) ->
    exists x y.
      (a=c+x \/ c=a+x) /\
      ((b=d+y \/ d=b+y) /\
       (exists k. x*x+y*y = p*k)).
```

All four natural-order branches are kernel-checked. Equal signs yield
`r*x == y (mod p)`; opposite signs yield `r*x+y == 0 (mod p)`.
Constructive additive cancellation proves the latter still implies
`(r*x)^2 == y^2 (mod p)`. The polynomial identity
`(r*r+1)*x^2 = (r*x)^2+x^2` then produces an actual divisibility witness,
without subtraction, excluded middle, or double-negation elimination.

The tranche additionally proves witnessed absolute differences, their
preservation of an existing coordinate bound, and

```
flat_square_index_row_below_width:
  forall w i j k.
    k = w*i+j -> k < w*w -> i < w.
```

The principal endpoint statement SHA-256 is
`b3923688b19701526842363879c8fbd5322a62ddf4dc62df5a10f63d032b8600`.
The complete candidate replay contains at most **358 proof nodes** and has
maximum proof depth **38**.

## Final prime-proof composition beyond this tranche

This tranche itself does not claim the full theorem
`Prime(p) /\ p == 1 (mod 4) -> exists x y. p=x*x+y*y`. The affine-grid
collision requires the following additional decoded composition:

1. Use `beta_at_unique` to identify both colliding affine remainders and
   `equal_affine_remainders_balanced` to obtain the balanced collision.
2. Convert both decoded row/column bounds `< S s` into `<= s`, then apply
   `bounded_natural_absolute_difference` to both witnessed differences.
3. Derive that the differences cannot both vanish from the distinct flat
   indices, and turn this into explicit strict positivity of their norm.
4. Apply the existing
   `prime_floor_bounded_divisible_norm_represents_prime` endpoint.

The subsequent
[`prime two-square theorem tranche`](fermat-two-squares-prime-rfc-v1.md)
now supplies and independently body-checks all four steps, yielding the
complete constructive prime endpoint. Neither tranche claims the separate
all-integer valuation classification, empty-context closure, Alpha admission,
or Stable promotion.
