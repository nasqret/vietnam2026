# RFC v1: constructive finite-prefix collision decision

Status: six isolated, independently kernel-checked, intuitionistic
dependency-curried candidates. None is a public theorem, a closed recursive
certificate, or an Alpha/Stable admission.

Implementation:

- `peano-lab/py/peano_lab/library/finite_prefix_collision_decision_candidate.py`
- `peano-lab/py/tests/test_finite_prefix_collision_decision_candidate.py`

## Exact constructive result

The previous two-square pigeonhole tranche established an oversized-domain
noninjectivity theorem but correctly distinguished `~InjectivePrefix` from an
existential collision. This tranche closes that distinction constructively:

```text
forall b c l.
  Collision(b,c,l) \/ InjectivePrefix(b,c,l).

forall b c l m.
  BoundedInto(b,c,l,m) -> m < l -> Collision(b,c,l).

forall b c l p s.
  l = (s+1)*(s+1) -> FloorSqrt(p,s) ->
  BoundedInto(b,c,l,p) -> Collision(b,c,l).
```

Here the collision is the actual expanded existential

```text
exists i j v.
  i < l /\ j < l /\ ~(i=j) /\
  BetaAt(b,c,i,v) /\ BetaAt(b,c,j,v).
```

No classical principle is used. Induction on the prefix length decodes the
final value, invokes the existing constructive finite-membership decision,
and either exhibits an earlier equal-value index or extends the old
injectivity proof. The oversized and floor-square endpoints compose that
decision with the previously verified pigeonhole obstruction.

## Independently checked candidates

| candidate | dependencies | commands | kernel nodes | depth |
|---|---:|---:|---:|---:|
| `finite_prefix_collision_succ` | 1 | 31 | 78 | 35 |
| `finite_prefix_last_occurrence_collision` | 3 | 28 | 57 | 27 |
| `finite_prefix_injective_extend_fresh` | 2 | 77 | 124 | 32 |
| `finite_prefix_collision_or_injective` | 7 | 60 | 76 | 25 |
| `finite_bounded_into_oversized_collision` | 2 | 17 | 43 | 24 |
| `floor_square_oversized_bounded_grid_collision` | 2 | 19 | 44 | 26 |

The exact endpoint statement hashes are:

```text
finite_prefix_collision_or_injective
34cd81f2d760771a7c74c6067f2356df3048d25a5212b2688f65cd77c5abae22

finite_bounded_into_oversized_collision
e6c0e6e5bd4b20bbb77b1e9071a39b63d8a908fd317c8be56bfe2ccfb8b77ee1

floor_square_oversized_bounded_grid_collision
d81e62ee6c37b580c87421ba7d9d9cbf1cf153cd7d3866f76ac01e27fe1fc6ed
```

All order, floor-square, boundedness, injectivity, collision, and beta-decoder
relations expand into unchanged first-order Heyting arithmetic before kernel
checking. The focused audit freezes names, dependencies, statement hashes,
structural receipts, public-registry isolation, false-target rejection,
absence of `DNE`, and 23 explicit numerical grid collisions.

```bash
PYTHONPATH=peano-lab/py python3 -m pytest -q \
  peano-lab/py/tests/test_finite_prefix_collision_decision_candidate.py
```

The bounded run passes **28 tests in 1.31 seconds**. The subsequent
[`affine residue-grid tranche`](fermat-two-squares-residue-grid-rfc-v1.md)
now constructs that particular grid and its actual collision. The separate
[`collision-to-norm tranche`](fermat-two-squares-collision-norm-rfc-v1.md)
proves all signed divisibility branches, and the
[`prime two-square theorem tranche`](fermat-two-squares-prime-rfc-v1.md)
completes bounded/nonzero difference extraction and the full constructive
prime endpoint. The all-integer classification and release admission remain
separate open gates.
