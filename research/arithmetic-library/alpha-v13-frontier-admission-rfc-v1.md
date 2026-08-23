# Alpha v13 constructive-frontier enrollment and evidence boundary

## Scope and immutable parent

Alpha v13 extends the sealed **1,303-row Alpha v12** ledger by precisely the
dependency-minimal constructive proof campaigns for the completed universal
Lagrange four-square theorem and the completed arbitrary-length Lucas theorem.
The existing **432-row Stable edition is preserved byte-for-byte** and remains
the default checked channel. Every existing Alpha v12 entry, its provenance,
evidence status, ordering, and release identity survives as an unchanged
prefix.

The reviewed roots and exact expanded-statement SHA-256 receipts are:

```text
four_square_lagrange
  fb653494c208dd59fac181164286a628866e3f7ca467e2a04314b9cb1f3c29a5

lucas_theorem
  396e47df462c415ea6ea8e29c7506bfb1dc7077a96e768295b1949256d9b0564
```

Both formulas are unconditional *statements*. Their scripts are verified as
dependency-curried kernel-checked bodies; Alpha enrollment does **not** turn
either script into an empty-context proof.

## Minimal dependency closure

The current constructive-frontier factories expose **464** distinct candidate
rows. Traversing the exact declared dependency graph, stopping only at already
enrolled Alpha v12 entries, gives:

| Campaign | New theorem bodies | Direct Alpha-v12 dependencies |
| --- | ---: | ---: |
| Universal Lagrange four-square theorem | 196 | 89 |
| Arbitrary-length Lucas theorem | 44 | 49 |
| Union | 240 | 109 distinct |

The two new-theorem closures are disjoint. Therefore exactly **240** new rows
are required, **224** unrelated candidate rows remain outside Alpha, and the
resulting Alpha v13 edition has **1,543** entries. The append order is
dependency-first depth-first postorder, first the 196-row Lagrange campaign,
then the 44-row Lucas campaign. The exact compact-JSON ordered-name SHA-256 is:

```text
333c10386d23959fa397e763e236daeadaae0d438a00489b0b089aeb8a4b0148
```

Order-independent sorted-name SHA-256 receipts are:

```text
Lagrange: 75fc0d5fe8bcc38bc98c04886889ccd6ade320cb7236bf72039593c2d03f6569
Lucas:    d842e9724e120f51a1bdbf80d771170b5a44fff93b1977e282bad6d314b0b9d4
Union:    f2be125fecc9dd1cb890edab33ab174c40bc3cc51c45f011c488424a492ecfda
```

The resulting sealed dependency graph has **5,189 edges** and **45 layers**.
Its exact ordered-enrollment identity is
`6b223edfe6a2e02dc09576671f4fc5f5a41aaf4156f829164222dd3e494da22f`; its full
Alpha-v13 edition identity is
`a010e0ee5dece0d3325e8ec084c1f8769ef8e9ca47e2de891d344e54c1b439d1`.

The sorted exact inventory of theorem names, source modules, expanded-statement
hashes, and ordered dependency lists has SHA-256
`e15f2d053a9d721988c13abc4543e07cdfbe71a6ceb8805d52e0db6503856df2`.

The minimal closure selects rows from **25** source factories:

```text
fermat_two_squares_classification_candidate         8
fermat_two_squares_collision_norm_candidate         3
fermat_two_squares_pigeonhole_candidate             2
finite_prefix_collision_decision_candidate          5
four_square_bounded_seed_candidate                  6
four_square_branch_descent_candidate                5
four_square_conjugate_identity_candidate            9
four_square_cross_pigeonhole_candidate              4
four_square_descent_candidate                      26
four_square_euler_candidate                        25
four_square_identity_candidate                     15
four_square_lagrange_bridge_candidate               3
four_square_lagrange_candidate                      3
four_square_lagrange_final_candidate                3
four_square_parity_selection_candidate             12
four_square_residue_intersection_candidate         17
four_square_signed_block_negative_candidate         2
four_square_signed_cases_candidate                 17
four_square_signed_orientation_candidate            3
four_square_signed_quaternion_candidate            28
lucas_block_digit_candidate                         5
lucas_convolution_candidate                        12
lucas_digit_candidate                               1
lucas_low_digit_candidate                           5
lucas_multidigit_candidate                         21
```

## Exact checked-use boundary

Every appended entry has:

```text
membership          alpha_only
enrollment_origin   ha
evidence_status     body_checked
body_checked        true
checked_use         false
empty_context_closure null
```

The **570** previously checked-use Alpha entries remain the only checked-use
entries. The existing one pending-layered-closure entry remains pending. The
new direct Alpha-v12 boundary consists of 77 `stable_closed`, 5 `alpha_closed`,
and **27 `body_checked`** prerequisite rows. The full transitive Alpha-v12
ancestor closure contains 183 `stable_closed`, 5 `alpha_closed`, and **53
`body_checked`** rows. Thus neither flagship can be exposed as a checked-use
theorem or claimed to have empty-context closure under the present evidence;
`replay()` must reject both roots. Neither Alpha v13 enrollment, artifacts,
receipts, nor explorer labels promote a theorem to Stable.

Each appended theorem must carry an actual fresh dependency-curried kernel body
receipt. Source statement/script hashes, dependency topology, artifact hashes,
membership labels, and receipt mutations are integrity evidence only; they do
not replace checking the proof body.

## Immutable Alpha-v12 artifacts

```text
artifacts/peano-library/alpha/catalog-v12.json
  825909e057492de87ef08208451c3475396ca009179c513457b05b57f7e2f109
artifacts/peano-library/alpha/metrics-v12.json
  64da675a3144f4bb0875c2e0650064e72d5d3eb613542d217719280addfaacb4
artifacts/peano-library/alpha/dependency-graph-v12.mmd
  583d18473200097997fa6b8ef0b57ebef9da95f136555d97b24220f1abb356b8
artifacts/peano-library/channels-v12.json
  0063b6d25f6f27869b00af0d7a31f53dda22d82e8d9c30779309939b46c60982
```

Alpha v13 receives new, separately named `catalog-v13.json`,
`metrics-v13.json`, `dependency-graph-v13.mmd`, and `channels-v13.json`
artifacts. Existing v12 and Stable bytes must never be rewritten.
