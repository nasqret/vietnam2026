# Complete constructive Bertrand-postulate proof receipt

The canonical artifact
`research/arithmetic-library/artifacts/bertrand-proof-bundle-v1.json` contains
an independently verified constructive proof of the exact immutable Alpha-v17
theorem `bertrand_strict`, with original statement

```text
forall n. (exists h. h + S 1 = n) -> exists p. ((~(p = 1) /\ forall a b. p = a * b -> a = 1 \/ b = 1) /\ ((exists u. u + S n = p) /\ (exists v. v + S p = n + n)))
```

Frozen independently checked artifact metrics:

- SHA-256: `84078d40d2df7b072938975191fb70c95731059ced716a12050df4376e2d4883`.
- Canonical UTF-8 bytes: **14,368,763** (approximately 14.4 MB).
- Exact theorem-body nodes: **544**, with root ID **543**.
- Exact original theorem dependency edges: **1,917**.
- Total independently checked kernel proof-body nodes: **187,725**.
- Exact immutable Alpha-v17 dependency statuses: **202** Stable closed,
  **12** Alpha closed, and **330** body-only.
- Genuine existing artifact proof bodies: **183** quadratic reciprocity,
  **3** supplementary-law, **33** Lucas, and **64** Kummer: **283** total.
- Fresh independently reconstructed theorem bodies: **261**, comprising
  **20** already-closed parent theorems and **241** body-only theorems.
- Deterministic actual reconstruction microbatches: **34**. Every batch keeps
  the unchanged limits of at most **16 rows**, **125,000 structural proof
  nodes**, and **25,000 distinct proof objects**.
- The original Python intuitionistic kernel checks every one of the **544**
  exact theorem bodies against its exact original theorem and dependency list.

One historical proof body requires an explicitly disclosed proof-only
normalization. The immutable enrolled theorem
`pow_two_seed_bundle_from_total` retains its exact original statement, its
exact original two dependencies `pow_successor_compose_from_total` and
`pow_two_base_two_value_four`, and its untouched **266-command** ledger script.
The historical script's two repetitive PA3–PA6 rewrite blocks for
`32 * 2 = 64` and `64 * 2 = 128` produce an actual proof annotation envelope
of depth 270, which cannot pass the unchanged canonical bundle depth cap of
256. The artifact instead constructs an independently checked proof of the
same exact curried statement by replacing only those two frozen rewrite blocks
with the pre-existing original-kernel-checked `norm_num` tactic. Only its
authoring-time AST-inspection depth allowance is increased to 192 to inspect
the existing unary numeral 128. The resulting proof has **1,594** structural
nodes, **1,594** proof objects, proof depth **145**, and combined
proof-and-annotation depth **206**, below the unchanged **256** cap. Its
canonical encoding/decoding and independent compiled Lean verification also
pass. No kernel rule, axiom, theorem statement, dependency, ledger script,
canonical codec bound, proof-envelope bound, or batch limit is changed.

Independent compiled Lean verification of the entire canonical artifact:

```text
ACCEPT  research/arithmetic-library/artifacts/bertrand-proof-bundle-v1.json  nodes=544  root=543
```

This receipt describes complete independently verified proof evidence only. It
does not by itself alter immutable Alpha-v17 authority, CheckedTheorem use,
Stable authority, or any release or deployment.
