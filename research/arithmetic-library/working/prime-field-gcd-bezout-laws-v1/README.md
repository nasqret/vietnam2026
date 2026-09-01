# Constructive Bézout laws for the gcd recursion

Working-only native source, with the unchanged ND0342 right-divisibility, ND0346 common-right-divisor and ND0347 Bézout expansions. Here `D |r A` means that an actual proper product `Q*D` is formally coefficient-equivalent to the canonical target A. It does not mean equality of beta codes or merely equality of evaluations.

The four rows, in source order, are:

1. `prime_field_polynomial_aligned_add_empty_right`: Prime(p) and canonical A give a genuine aligned sum A + empty = A, by constructing a zero prefix at A's length.
2. `prime_field_polynomial_bezout_from_right_multiple`: Prime(p), canonical B and A |r G give an actual coefficient U with Bézout(A,B,G,U,empty). The quotient already witnessing A |r G is retained, and the empty coefficient's product with B is constructed.
3. `prime_field_polynomial_bezout_equivalent_transport`: for p != 0, independently equivalent canonical replacements A', B', G' preserve the same coefficients U,V. The two new proper products are constructed and their output equivalences proved. No primality, equal lengths, raw-code equality or supplied output-product equality is required.
4. `prime_field_polynomial_bezout_common_right_divisor`: Prime(p), CommonRightDivisor(D,A,B) and Bézout(A,B,G,U,V) imply D |r G. It uses actual left-product divisibility followed by aligned-add closure, without polynomial commutativity.

The last law is a greatestness implication, not an assertion that every Bézout representative is itself a common divisor. This directory introduces no gcd or normalization definition and does not prove recursive gcd existence by itself. The main recursion must separately retain CommonRightDivisor(G,A,B) and zero-or-monic G.

## Exact source and focused validation

- Source: 15,300 bytes, SHA256 `76b90226e5e29fdde3d9bb49accccf8d9b4c0cc17a4de406af253e999102533c`.
- Test: 20,903 bytes, SHA256 `21da40c3b70a9eb3436b681cfdfd99a2278786dea73b4e5bfdfdefaccdd1b7e0`.
- Ordered four-spec SHA256: `cbf875f3e7d13394f062e4f5f4349beba59a2ac363a599e7b02649906ea6d6a2`; 21 direct prerequisites and 465 commands (67,109,208,81).
- 320 distinct focused cases passed: 250 independent expanded-contract/beta-model/source cases, four positive original conditional HA cases, and 66 rejection cases; 960 passed phases, no skips or xfails.
- Ordered test-ID SHA256: `b611e3453bae1ce9a0d8e584e04a3094ce405a2491a2d23c0b2b0a358bc2439b`.

| Positive row | Proof nodes / depth | Process seconds | Peak RSS bytes |
| --- | ---: | ---: | ---: |
| Aligned empty right | 85 / 39 | 5.044553 | 115,032,064 |
| Terminal right multiple | 144 / 63 | 9.063524 | 142,524,416 |
| Equivalent transport | 241 / 86 | 31.288939 | 291,176,448 |
| Common-divisor greatestness | 237 / 101 | 11.219997 | 169,279,488 |

All processes retained the original CPU 170/175-second, wall 180-second, RSS 1,536-MiB and live-proof-depth 256 bounds. The six disjoint negative windows had 24, 14, 12, 6, 6, 4 cases. Source/test bytes and the whole old95 directory stayed unchanged throughout. No positive was rerun to complete the rejection suite.

[Development observations](development-observations-v1.json) preserve the exact commands, all four actual conditional receipts, the pure/model run and collection metadata. They also preserve a failed ephemeral runner whose incorrectly named pytest hook stopped before any collection, test or proof call; it receives zero credit. [Final focused observations](focused-validation-observations-v1.json) preserve all six rejection-window reports and the complete case accounting. [Evidence reconciliation](evidence-reconciliation-v1.json) independently checks the stored pins, case IDs, receipts, bounds and preservation without replaying a proof.

Conditional HA means the declared dependencies were ordinary hypotheses during these isolated body checks. These are not dependency-complete bundle, compiled-Lean, Alpha-admission, publication or full G091/gcd-completion claims. The existing proof gates, kernel, canonical runtime and all prior checkpoints were left unchanged.
