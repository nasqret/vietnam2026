# RFC v1: constructive square-root grid and rectangular pigeonhole bridges

Status: twelve isolated, independently kernel-checked, intuitionistic
dependency-curried proof bodies. These candidates are neither registered
public theorems nor Alpha/Stable edition promotions. In particular, this
tranche does **not** claim the complete Fermat two-square theorem.

Implementation:

- `peano-lab/py/peano_lab/library/fermat_two_squares_pigeonhole_candidate.py`
- `peano-lab/py/tests/test_fermat_two_squares_pigeonhole_candidate.py`
- Previous stage:
  `peano-lab/py/peano_lab/library/fermat_two_squares_candidate.py`.

## Constructive endpoint

The existing first supplementary law constructs, for every prime
`p = 1 mod 4`, a root `r < p` of `-1` modulo `p`. The previous two-square
foundation showed `p | r*r + 1`, but correctly noted that this particular
norm need not be below `2*p`.

The present tranche changes the precise remaining mathematical gap. Let
`s = floor_sqrt(p)`. It now independently proves:

```text
Prime(p) -> FloorSqrt(p,s) -> a <= s -> b <= s ->
  a*a + b*b < p+p.

Prime(p) -> FloorSqrt(p,s) -> a <= s -> b <= s ->
  0 < a*a+b*b -> p | a*a+b*b -> p = a*a+b*b.
```

Consequently the previous separate strict-norm inequality is no longer a
missing premise once both coordinates lie in the floor-square grid. The only
remaining representation inputs are a **nonzero**, **divisible** pair of
coordinates bounded by `s`.

Independently, totality of the already checked Bertrand floor-square relation
provides an explicit grid side and its cardinality overflow:

```text
forall p. exists s.
  FloorSqrt(p,s) /\ p < (s+1)*(s+1).
```

The constructive rectangular pigeonhole bridge is also proved:

```text
BoundedInto(code,scale,l,n) -> n < l -> ~InjectivePrefix(code,scale,l).
```

Here `BoundedInto` stores an actual beta-decoded value below `n` for each
index below `l`. This is not an appeal to classical cardinality: the proof
restricts the map to its first `n` entries, applies the existing checked
square finite-pigeonhole theorem to an assumed injection, obtains a preimage
for the decoded value at index `n`, and derives the explicit contradiction
`n < n`.

Specializing to `l = (s+1)*(s+1)` yields:

```text
FloorSqrt(p,s) ->
BoundedInto(code,scale,(s+1)*(s+1),p) ->
~InjectivePrefix(code,scale,(s+1)*(s+1)).
```

## First-order surface

All displayed abbreviations are expanded before parsing into unchanged
first-order Heyting arithmetic:

```text
a < b                := exists h. h + S(a) = b
a <= b               := exists h. h + a = b
Prime(p)             := ~(p=1) /\
                        forall u v. p=u*v -> u=1 \/ v=1
FloorSqrt(p,s)       := (exists h. h+s*s=p) /\
                        (exists k. k+S(p)=S(s)*S(s))
p | z                := exists q. z=p*q
```

`BoundedInto`, `InjectivePrefix`, and the explicit collision relation use the
pre-existing expanded beta decoder; no floor-square function, finite-set type,
new predicate symbol, quotient function, classical axiom, or kernel change
occurs.

## Exact checked candidate tranche

| candidate | dependencies | commands | kernel nodes | maximum depth |
|---|---:|---:|---:|---:|
| `prime_is_not_natural_square` | 0 | 21 | 89 | 17 |
| `natural_square_monotone_expanded` | 3 | 21 | 24 | 13 |
| `prime_floor_square_strictly_below_prime` | 2 | 19 | 23 | 13 |
| `prime_floor_bounded_coordinate_square_strict` | 3 | 23 | 27 | 15 |
| `two_strict_values_sum_below_double` | 3 | 23 | 103 | 35 |
| `prime_floor_bounded_two_square_norm_below_double` | 2 | 30 | 36 | 19 |
| `floor_square_successor_grid_strictly_exceeds_input` | 0 | 5 | 12 | 8 |
| `floor_square_oversized_grid_exists` | 2 | 12 | 14 | 10 |
| `prime_floor_bounded_divisible_norm_represents_prime` | 2 | 27 | 34 | 22 |
| `finite_bounded_into_oversized_not_injective` | 4 | 88 | 117 | 33 |
| `floor_square_oversized_bounded_grid_not_injective` | 2 | 23 | 29 | 19 |
| `finite_bounded_into_collision_from_constructive_decision` | 1 | 18 | 35 | 22 |

The exact graph digest, incorporating candidate order, statements,
dependencies, and scripts, is:

```text
4c2306775e0da73eb56c56c25e0c1acbfdc5e38a4732db4232554d69a86a7e80
```

The largest candidate body contains 117 proof nodes; maximum depth is 35.
Every dependency-curried certificate is independently checked from empty
context for its exact implication, every proof object is audited for absence
of `DNE`, and each declared dependency is individually mutated to the false
contract `0=1` and rejected.

## Exact remaining blocker

Intuitionistically, `~InjectivePrefix` is **not** the same as an existentially
witnessed collision. The final checked candidate proves only the honest
conditional bridge:

```text
BoundedInto(code,scale,l,n) -> n < l ->
(Collision(code,scale,l) \/ InjectivePrefix(code,scale,l)) ->
Collision(code,scale,l).
```

Thus the complete root-to-representation step still requires three genuine
constructive additions:

1. Constructively decide collision versus injectivity for a beta-coded finite
   prefix, using bounded equality decisions and beta-decoder functionality.
2. Beta-code the two-dimensional residue grid
   `(i,j) |-> canonical_remainder_p(r*i+j)` for `0 <= i,j <= s`; the existing
   prefix-extension and division/remainder machinery supplies the likely route.
3. Transport an actual collision to distinct bounded grid coordinates, choose
   signed coordinate differences constructively, and prove their nonzero
   two-square norm is divisible by `p` from `r*r = -1 mod p`.

Subsequent checked tranches have since completed item 1 in the
[`finite-prefix collision decision RFC`](finite-prefix-collision-decision-rfc-v1.md)
and item 2 in the
[`affine residue-grid RFC`](fermat-two-squares-residue-grid-rfc-v1.md). The
[`collision-to-norm RFC`](fermat-two-squares-collision-norm-rfc-v1.md) also
proves all four signed divisibility branches and grid row bounds, and the
[`prime two-square theorem RFC`](fermat-two-squares-prime-rfc-v1.md)
completes simultaneous bounded/nonzero witness extraction and final
composition. The all-integer valuation classification is still separate.

After those additions, the already checked
`prime_floor_bounded_divisible_norm_represents_prime` immediately closes the
prime two-square theorem. No release metadata is changed or implied here.

## Reproduction

From `peano-lab/py`:

```bash
python3 -m pytest -q tests/test_fermat_two_squares_pigeonhole_candidate.py
```

The bounded suite checks deterministic candidate order, frozen statement and
graph hashes, native first-order closure, public-registry isolation,
dependency order, exact kernel receipts, independent false-target rejection,
absence of double-negation elimination, every-edge false-contract mutation,
eleven prime floor-grid bounds, eleven actual two-square examples, and
nineteen host-side oversized-map collision sanity checks. It does not execute
a large layered closure, contact the remote cluster, or mutate Alpha/Stable.
