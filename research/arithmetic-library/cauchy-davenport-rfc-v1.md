# G051: constructive Cauchy–Davenport with actual finite sumsets

This additive candidate proves the full prime-field sumset bound by an
elementary Dyson-transform argument. It does not assume a polynomial-method
oracle, an unspecified finite-set interface, a cardinality oracle, or a
choice principle. All sets, translations, unions, intersections, and exact
cardinalities used in the proof have actual beta-coded witnesses.

The unchanged Alpha v26 catalogue is the sole admitted parent. The two new
factories must be read in order:

1. `make_finite_modular_set_candidate_theorems`: 49 finite-set and counting
   foundations;
2. `make_cauchy_davenport_candidate_theorems`: 23 orbit, Dyson-descent, and
   full Cauchy–Davenport results.

## Exact statement and finite-set domain

A finite subset of the canonical residues `0,...,p-1` is represented by two
natural beta-code parameters. `FiniteModularSet(b,c,p,k)` is exactly the
existing `BitCount(b,c,p,k)`: an actual finite sum trace, together with the
proof that all `p` decoded values are zero or one. Membership requires an
index below `p` whose decoded value is one. Raw code equality is never used
as set equality.

`ModularSetSum(A,B,S,p)` says that every canonical residue is in `S` if and
only if it is congruent to the sum of an actual member of `A` and an actual
member of `B`. Both directions, both membership witnesses, and all canonical
bounds are present in the expanded first-order formula.

The exact G051 endpoint `prime_cauchy_davenport_sumset_bound` states:

```text
forall p b c d e sb sc k l m.
  Prime(p) ->
  FiniteModularSet(b,c,p,k) ->
  FiniteModularSet(d,e,p,l) ->
  FiniteModularSet(sb,sc,p,m) ->
  k != 0 -> l != 0 ->
  ModularSetSum(b,c,d,e,sb,sc,p) ->
  (p <= m or k+l <= S m).
```

The conclusion is the subtraction-free natural-arithmetic form of
`m >= min(p,k+l-1)`. It is sharp and includes the prime `p=2`, singleton
inputs, and full residue sets. Neither input is required to contain zero.
Primality and both nonemptiness guards are essential; tests include explicit
counterexamples when those guards are removed.

The stronger intermediate `prime_cauchy_davenport_cover_bound` only assumes
that `S` contains every input sum. The independent constructive endpoint
`prime_cauchy_davenport_sumset_exists` constructs the beta code of the exact
sumset, its exact count, and the sharp bound together. Thus the theorem is
usable without first supplying an opaque sumset code or its cardinality.

## Conservative definition DAG

All new surfaces expand to the original first-order HA signature. No new
kernel predicate or term former is introduced. Global definition identities
are allocated separately by the integration owner.

The finite-set module exposes these eight surfaces:

- `finite_modular_set_relation`: existing `Sum` and `AllBits` via `BitCount`;
- `modular_set_member_relation`: strict natural bound and actual beta value;
- `modular_set_subset_relation`: bounded characteristic membership implication;
- `modular_set_union_relation`: exact bounded disjunction of membership;
- `modular_set_intersection_relation`: exact bounded conjunction of membership;
- `modular_set_pullback_relation`: canonical membership transported by balanced
  congruence; its target is the source set minus the supplied shift;
- `modular_set_sum_cover_relation`: all actual input sums belong to the target;
- `modular_set_sum_relation`: exact all-and-only sumset membership.

The Cauchy–Davenport module adds:

- `modular_translation_boundary_relation`: an actual in-set source, an actual
  canonical shifted target, and constructive nonmembership of that target;
- `modular_dyson_transform_relation`: the exact upper/lower transformed sets,
  using actual translated membership witnesses;
- `cauchy_davenport_bound_relation`: only the two witness-defined natural
  inequalities in the sharp conclusion.

The bottom-up dependency structure is:

```text
BetaAt + natural order + balanced congruence
  ├─ actual characteristic membership
  ├─ AllBits + witnessed Sum → exact finite cardinality
  │    ├─ subset/proper-subset counting
  │    └─ union/intersection exact count balance
  └─ canonical remainder codes + beta composition
       └─ bounded injective translation indices
            └─ finite Sum permutation invariance
                 └─ actual translated sets with unchanged count

actual unions + actual translations + finite prefix induction
  └─ actual exact sumset code and count

prime modular inverse + finite first-exit induction
  └─ witnessed nonzero-direction translation boundary

union/intersection + translated sets + boundary
  └─ actual Dyson pair with equal total size and smaller second size
       └─ bounded natural induction → normalized sharp bound
            └─ opposite translations → full G051
```

Tests compare all eleven public expansions against independently handwritten
primitive formulas, not just a second use of the same helper. A dedicated
nested-binder regression checks that the second input index of a partial
sumset remains the actual summand and is never captured by a modular-witness
binder. Reserved names, duplicate arguments, invalid terms, and generated
binder prefixes are rejected by the public surfaces.

## Actual finite construction and strict descent

The coding layer constructs intersections by pointwise products of bit
prefixes, and unions by actual characteristic complements and intersections.
Constructive finite membership decisions justify the De Morgan step. An
ordinary finite-sum induction proves the four-prefix balance, and the
checked Boolean truth table gives `|A union B|+|A intersection B|=|A|+|B|`.

Canonical translation indices are built from a genuine range prefix followed
by actual quotient/remainder recoding. A separate beta-composition induction
constructs the translated bit prefix. Boundedness and injectivity of the
index code supply the existing finite-permutation sum theorem, so unchanged
cardinality is proved rather than postulated.

The exact sumset constructor runs an induction through the second input's
characteristic prefix. An absent bit changes nothing. A present bit adjoins
the genuinely translated first set to the current coded union. Every stage
has an exact two-way membership invariant and an actual count.

For the main theorem, translate both inputs in opposite directions so that
zero is in the second set, while preserving both counts and every sum.
If the upper sumset is full, the bound is immediate. The singleton case is
actual subset counting. Otherwise select a genuine nonzero second-set
member `h` and a residue outside the first set. A bounded modular inverse
constructs an additive orbit reaching that outside residue; ordinary orbit
induction constructs a first exit `e -> e+h`.

Construct

```text
Ae = A union (B+e)
Be = B intersection (A-e).
```

The implementation first constructs `T=B+e`, then `U=A union T`,
`I=A intersection T`, and `V=I-e`. It proves that `U,V` have exactly the
displayed Dyson semantics. Actual permutation counting proves
`|Ae|+|Be|=|A|+|B|`. Zero belongs to `Be`, whereas the boundary direction
`h` does not. The proper-subset counting theorem therefore proves
`0 < |Be| < |B|`, and `Ae` is nonempty.

Every sum from `Ae+Be` belongs to the original upper sumset. The translated
case uses `(b+e)+v=b+(v+e)` in balanced modular arithmetic with actual source
witnesses. Bounded ordinary induction on the second cardinality completes
the sharp bound. There is no imported strong-induction oracle.

## Exact evidence and release boundary

All 72 dependency-curried proof bodies pass the unchanged original kernel
in one complete bounded check:

| Part | Rows | Direct edges | Commands | Proof-node occurrences | Maximum depth |
| --- | ---: | ---: | ---: | ---: | ---: |
| Finite modular sets | 49 | 156 | 2,928 | 4,807 | 65 |
| Cauchy–Davenport | 23 | 99 | 1,698 | 2,423 | 78 |
| Combined | 72 | 255 | 4,626 | 7,230 | 78 |

Every declared edge is used by its body. No old candidate, checked theorem,
kernel, trusted checker, edition, release artifact, explorer, or deployment
is modified by this tranche.

The two focused suites pass **144 tests** in one bounded process, including
the complete original-kernel body replays, every forged-body rejection,
independent primitive-definition audits, guard mutations, and numerical
boundary regressions.

Ordered names SHA-256:

```text
finite49  27e2e5f74640a12182409fb60c6828aaa9f2e54bcae68d5cfa3d294c1064049c
cauchy23  bc5d1ae5154493dd5f86c8606084cb7bfc087070dc36be11de3c2ce7c309d86e
```

Exact major statement SHA-256:

```text
finite_modular_sumset_exists
46420a141069c2696880ec30397f7cedaa2c8b7866ddc2791ec2aff0c799a9d9

finite_modular_dyson_transform_exists
b26bc5fc26d6f7f8f12183a0805b69b6d9c2f93c94727641d1bd9b89be09b012

prime_cauchy_davenport_sumset_bound
634e3a5403ad025cef1e894dc2b9c3401691bb84bb57c2b70cb3aba185b806fb

prime_cauchy_davenport_sumset_exists
7f2babcbea49f9ebe8e3a5d2339d0009d16d61afbe33341fcf7b951ede80b6e1
```

Tests reconstruct dependency hypotheses from the unchanged v26 catalogue,
pinned to SHA-256
`969c261f924060552dda393427b4fbc51515b9d4e69daa17f5e9f1691b5ab534`,
to avoid eagerly loading every historical proof provider. This is an
authoring memory bound, not a new source of theorem authority. Numerical
checks of all nonempty subset pairs for primes through seven, first-exit
orbits, translation invariance, and sharp interval examples are regressions
only.

Dependency-closed original-kernel certificates and independently compiled
Lean proofs remain the integration owner's mandatory admission gate. Body
acceptance alone does not promote Alpha, change the published G051 status,
or establish a deployment claim. The blueprint's conceptual polynomial
route should be updated honestly to this actual Dyson/finite-counting route
when those closure checks succeed.
