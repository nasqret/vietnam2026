# Polynomial Euclidean division and the route to gcd/Bezout

This is a working research directory, not a production library registration.
Current Alpha v32 has 3,971 checked-use theorems; Stable remains the default
432. None of the new statements in this directory has been admitted to either
edition or installed in a public proof explorer.

## Verified 113-theorem checkpoint

The six tranches contain 8 triangular-convolution, 30 representation,
25 division-construction/identity/degree, 18 distributivity, 9 execution-
uniqueness and 23 convolution-padding lemmas. All 113 are new relative to
Alpha v32; the previous 81 are not counted as inherited Alpha.

The [complete extension bundle](artifacts/working-euclidean-extension-proof-bundle-v1.json)
contains 254 inherited Alpha theorems, 113 working theorems and one packaging
root: 368 nodes, 1,033 edges and 29,292 body-proof nodes. Its 2,219,445 bytes
have SHA-256
`c2e097f0e04c4b4f01bb219102405d0e93bc847c19625113eb48e55c7900734d`.
Every body passed original HA; independently compiled Lean accepted the
exact same bytes. Global comparison against all 3,971 Alpha statements
found no exact-AST duplicates. All 253 final integration guards passed.

All four separate ordinary-principal checks also passed: actual execution
functionality, actual execution existence-and-uniqueness, two-factor padding
equivalence and actual padded-product construction. Each freshly rechecked
the complete bundle and its exact ordinary empty-context certificate. The
five final windows totalled 229.527 seconds; no individual window exceeded
50.093 seconds or 1,319,944,192 bytes RSS. Original limits were unchanged.
The earlier 81-row artifact and all its frozen inputs remain unchanged.
The [complete 113-row observations](working-113-verification-observations-v1.json)
record all five actual reports, exact source/artifact identities and
reproduction commands. Saved observations do not grant proof authority.

## Preserved verified 81-theorem checkpoint

The four frozen tranches contain 8 triangular-convolution, 30 representation,
25 division-construction/identity/degree and 18 distributivity lemmas. The
complete bundle contains 232 inherited theorems, these 81 new theorems and
one packaging root: 314 nodes, 822 edges and 21,794 body-proof nodes.

Every body passed the original HA checker; the independently compiled Lean
checker accepted exactly the same bytes. All eight selected ordinary,
empty-context certificates also passed. The actual 3,971-entry comparison
found no duplicate new statements. The exact source identities, all nine
verification reports, limits and certificate sizes are in
[the observations ledger](working-81-verification-observations-v1.json).
That ledger is not consumed by any proof or admission gate.

The checked [proof bundle](artifacts/working-prime-field-euclidean-proof-bundle-v1.json)
has SHA-256
`3614e9504b84cfd24a52780d54ddc9eb16e49bf2df996c99664c9427e9a9fd83`.
The proof-bound RFC remains its exact authoring-stage snapshot; the separate
ledger records the subsequent completed checks without rewriting that input.

### What the division theorem actually establishes

Coefficients are canonical natural representatives modulo a prime, encoded
by actual beta prefixes in highest-degree-first order. Given an input of
length `L` and a divisor of length `S d` with nonzero leading coefficient,
the proof constructs quotient length `q = max(L-d,0)`, its actual triangular
quotient execution, an ambient product `P`, a residual `U`, and a trimmed
remainder `R`. The quotient and residual are not oracle values.

The proved coefficient identity is `A = P + U` at the common ambient length.
When the quotient is nonempty, `P` is the proper convolution `Q*B`; otherwise
it is an actual all-zero ambient prefix. `Trim(U,R)` removes actual leading
zeros. A separate representation theorem proves that `U` and `R` have the
same coefficient at every formal power. The remainder is empty, or has a
represented degree strictly less than `d`; degree is never assigned to zero.
Short and empty inputs, constant divisors and characteristic two are covered.

This is not a claim that an arbitrary cross-length addition/product API or
arbitrary formal-identity quotient/remainder uniqueness has already been
proved. Those representation-algebra statements have their own proof work.

## Conservative definitions and separate DAGs

[The definition registry](working_euclidean_definitions.py) adds exactly seven
aliases over all 390 unchanged inherited identities:

| ID | Name | Actual data described |
| --- | --- | --- |
| ND0334 | `PolynomialLeftPad` | Leading zeros followed by copied source coefficients |
| ND0335 | `PolynomialPowerCoefficient` | The coefficient of a formal power, with exterior zero |
| ND0336 | `PolynomialEquivalent` | Coefficientwise equality across representation lengths |
| ND0337 | `FpPolynomialQuotientStep` | Subtraction and scalar multiplication; the full execution supplies the inverse |
| ND0338 | `FpPolynomialQuotientPrefix` | The actual finite triangular execution |
| ND0339 | `PolynomialQuotientLength` | The zero/positive quotient-length alternatives |
| ND0340 | `FpPolynomialDivisionExecution` | Quotient, ambient convolution, subtraction and trim data |

The working registry has 397 definitions and 865 expansion arrows. All 92
notation tests pass: independent lower-vocabulary expansions, exact AST
round trips, binder hygiene, large numerals, novelty, historical preservation
and actual occurrence in working theorem statements. Definition imports do
not invoke theorem factories or grant proof authority.
The [fresh notation-check observations](working-definition-validation-observations-v1.json)
retain the exact command and source identities, not acceptance authority.

[The additive DAG adapter](working_euclidean_definition_graph.py) keeps
definition-expansion edges distinct from theorem-proof prerequisites. In
particular, the quotient identity, remainder-degree bound, primality and
formal polynomial equivalence are not hidden premises of the division
execution definition. Right padding is multiplication by a power of `X`,
not harmless left padding. Equality of evaluations in a finite field is
not substituted for formal coefficient equality.

## The additional 32 lemmas and the gcd/Bezout boundary

Nine execution-uniqueness and 23 convolution-padding lemmas have passed
their separate focused suites: 379 and 594 cases respectively, including
every actual HA body and rejection of each removed or poisoned dependency.
They are not part of the frozen 81-row bundle. Their separate 113-row
dependency-closed bundle has passed complete HA, same-byte compiled Lean
and all four additional ordinary-principal gates.

The focused evidence is retained separately for
[execution uniqueness](working-9-execution-uniqueness-observations-v1.json)
and [convolution padding](working-padding23-focused-observations-v1.json).
The [v32 UI regression ledger](current-alpha-v32-ui-observations-v1.json)
records all 1,053 passing cases, including seven actual Lean compilations.
These saved observations are not inputs to any proof or admission gate.

`DEFERRED_division_identity_converse.txt` is an explicitly unexecuted design
draft, outside all checked theorem factories and artifact inventories.

The intended next route is formal-equivalence congruence for actual
convolution, genuine associativity and scalar/unit products, then actual
divisibility and linear-combination witnesses. The Euclidean backward step
keeps the factor order explicit:

`A = Q*B + R`, `G = U*B + V*R` imply `G = V*A + (U-V*Q)*B`.

The induction will run on the second reduced length. A nonzero terminal gcd
is normalized by a proved unit action, not asserted equal to its unnormalized
source. `gcd(0,0)=0`, characteristic two, arbitrary beta encodings and
coefficientwise uniqueness must remain explicit. Bezout coefficients are
not unique. Full polynomial gcd/Bezout and the G091 prime-power-field endpoint
are not yet proved here.

### Next unproved representation contracts

The current padding theorems start from actual `PolynomialLeftPad` witnesses;
they do not yet accept arbitrary `PolynomialEquivalent` inputs. A read-only
API review identifies the following proposed bridge, before associativity:

1. `prime_field_polynomial_equivalent_implies_left_pad`: formal equivalence
   of lengths `L` and `t+L` implies that the latter representation is the
   actual `t`-entry left padding of the former. This needs no primality.
2. `prime_field_polynomial_add_equivalent_congruent`: over a prime field,
   actual aligned sums on equivalent input representations have formally
   equivalent outputs, including different alignment lengths.
3. `prime_field_polynomial_subtract_equivalent_congruent`: the corresponding
   statement for actual subtraction graphs.
4. `prime_field_polynomial_convolution_equivalent_congruent`: for nonzero
   modulus, two actual convolutions of pairwise formally equivalent factors
   have formally equivalent outputs, including unequal lengths and empty
   factors. Mixed length-order directions need a constructed cross-product.

These are proposed contracts, not checked rows. Their implementations should
reuse the proved same-length transports, padding compatibility and formal-
equivalence laws. They do not replace the separate triple-index finite-sum
reindexing proof needed for convolution associativity.

## Rechecking this frozen checkout

From the repository root, with its pinned independently built Lean companion:

```sh
python3 research/arithmetic-library/working/prime-field-euclidean-v1/check_working_euclidean_extension.py --task bundle
python3 research/arithmetic-library/working/prime-field-euclidean-v1/check_working_euclidean_extension.py --task root --name prime_field_polynomial_division_execution_exists_unique
```

Run each of the four names in
`working_euclidean_extension_support.PRINCIPAL_ROOTS` in its own root
window. Each rechecks the complete 368-node artifact before independently
materializing and checking its ordinary empty-context certificate.

The preserved 81-row checkpoint remains separately reproducible:

```sh
python3 research/arithmetic-library/working/prime-field-euclidean-v1/check_working_euclidean.py --task bundle
python3 research/arithmetic-library/working/prime-field-euclidean-v1/check_working_euclidean.py --task root --name prime_field_polynomial_division_execution_exists
```

Run each of the eight names in `working_euclidean_support.PRINCIPAL_ROOTS`
in its own root window. Each window rechecks the complete bundle first and
rebinds the exact sources afterward. The original CPU, wall, RSS, HA and
compiled-Lean limits are unchanged; no saved report substitutes for a check.
