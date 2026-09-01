# Actual left-constant polynomial multiplication

This working checkpoint contains six conditional Heyting-arithmetic bodies
and **332 distinct focused tests, all passed**. It is not a dependency-complete
bundle, an independent Lean verification, an Alpha admission, or a gcd/Bézout
endpoint. Existing source, kernel, runtime, catalogue and historical artifacts
were not changed.

## Mathematical contract

Representations are highest-degree-first beta-coded prefixes. Let
`K=(kb,kc,1)`, `A=(ab,ac,L)` and `H=(hb,hc,L)`.

The principal bridge is

```text
Prime(p) → Coeff(p,K) → BetaAt(K,0,k) → Scale(p,k,A,H)
  → Product(p,K,A,H).
```

The singleton is the **left** factor. The output uses the actual supplied
scalar-output codes, and has proper product length `L`, including `L=0`.
No multiplication-commutativity hypothesis is used. The converse derives
`Scale(p,k,A,H)` from an actual product and the singleton's actual head value;
its canonical scalar bound comes from `K`, even if the output is empty.

The constructor takes `Prime(p)`, `k<p`, and `Coeff(p,A)`, and returns actual
singleton and output codes with all four facts: canonical singleton, head
value `k`, scalar action, and genuine left-factor product. It includes scalar
zero and characteristic two. A zero scalar does not trim a nonempty product
to length zero. Decoded coefficients are constrained only inside the declared
prefixes; beta-code equality is never concluded.

The natural helper proves that the first antidiagonal term is the ordered
natural product `k*a`. It reuses the frozen value-independent
`polynomial_diagonal_left_unit_tail_term` for every later term, constructs an
actual one-term sum, and applies the existing zero-tail sum invariant. The
natural total may exceed `p`; the field coefficient is its bounded residue.

## Exact source inventory

| Theorem | Commands | Dependencies | Observed nodes/depth |
| --- | ---: | ---: | ---: |
| `polynomial_diagonal_left_constant_first_term` | 42 | 2 | 78 / 46 |
| `polynomial_diagonal_left_constant_natural_sum` | 137 | 11 | 242 / 52 |
| `prime_field_convolution_coefficient_left_constant` | 45 | 1 | 56 / 40 |
| `prime_field_polynomial_left_constant_product_to_scale` | 74 | 4 | 107 / 41 |
| `prime_field_polynomial_scale_to_left_constant_product` | 110 | 9 | 185 / 53 |
| `prime_field_polynomial_left_constant_product_exists` | 62 | 5 | 85 / 38 |

Total: six rows, 470 tactic commands and 32 declared dependency edges.
The exact ordered specification SHA-256 is
`736cd0d7d21f33ac50a189f66a7457909042c83917d9e9cfc2d4932c6fe06836`.

Frozen source: 17,620 bytes,
`9a7a4de30f5f389bcabc2e6267a0d2cc5dc5f061059dcea303a0a03dab58509a`.

Frozen test: 27,847 bytes,
`cc93a6d0b8d1ff3eae9bc0b16527936301a7a15e13e7baae3cf818a919cc6a60`.

## Validation boundary

The four clean windows contain 214 source/contract/native-beta model cases,
six original-HA positive cases, 48 false/incomplete/changed-input or
stronger-output cases, and 64 removed/poisoned dependency cases. Fresh
collection reconciled exactly 332 unique IDs and 996 actual passed pytest
phases, with no duplicate credit. All 32 edges were tested in both hostile
modes. Expected formulas were expanded independently of production graph
builders. Models include empty and all-zero inputs, arbitrary outside-prefix
values, distinct encodings, unbounded natural sums, characteristic two,
composite-modulus diagnostics, and concrete false-claim counterexamples.

Clean-window elapsed time summed to 38.35999041690957 seconds; the largest
window was 20.549648582935333 seconds and the largest observed peak RSS was
67,518,464 bytes. Every process retained CPU 170/175 seconds, wall 180 seconds,
RSS 1,536 MiB, and the unchanged depth-256 guard. No external timer wrapper
or larger limit was used.

The first development run correctly rejected row 3 because `zero_add` was
used but absent from its dependency list. The exact failed source identity,
command, metrics and partial observations are retained with zero completed
suite or additional-test credit. Adding the required edge was the only
post-diagnostic source correction. All six corrected bodies then passed.

`conditional-verification-observations-v1.json` records source pins, exact
ordered test IDs, losslessly encoded phase records, command templates, each
window's actual outcome/resources and the failed development incident.
It is **non-authorizing accounting only** and must never be accepted as a
proof or publication capability. Complete-cone and Lean checks remain future
work. No new definition alias or public page was registered.
