# Independently checked complete Lagrange four-square proof receipt

Date: **2026-08-25**.

The exact unconditional constructive theorem

```text
four_square_lagrange
```

now has a complete self-contained proof accepted independently by the existing
intuitionistic Python kernel and the separately compiled Lean proof-bundle
verifier. In addition, its entire 390-node dependency graph has been compiled
into **one ordinary existing-kernel `Cut` certificate**, and that unchanged
intuitionistic kernel has independently accepted the exact theorem from the
empty context. Its frozen original first-order Heyting-arithmetic statement is:

```text
forall n.
  exists a b c d.
    n = a * a + b * b + c * c + d * d
```

This theorem includes zero and every positive natural number. It assumes no
prime representation, strict descent, quaternion identity, modular seed, or
classical principle: each required result is proved inside the same exact
self-contained dependency graph.

No new axiom, kernel rule, `DNE`, trusted theorem-name lookup, host-arithmetic
oracle, proof digest, or `sorry` is accepted as logical evidence.

## Immutable Alpha-v17 source and release boundary

| Property | Independently checked value |
|---|---|
| Existing theorem name | `four_square_lagrange` |
| Frozen parent edition | Alpha v17 |
| Frozen parent identity SHA-256 | `db2e6e5796169600d17cc54313e9306bac46fb680f914cb2a5a91d247bb746c4` |
| Exact root statement SHA-256 | `fb653494c208dd59fac181164286a628866e3f7ca467e2a04314b9cb1f3c29a5` |
| Exact theorem/dependency nodes | `390` |
| Exact dependency edges | `1,187` |
| Original Stable-closed rows | `166` |
| Original Alpha-closed rows | `23` |
| Original Alpha-v17 body-only rows now actually proved | `201` |
| Four-square campaign rows among those proofs | `196` |
| Older body-only prerequisites among those proofs | `5` |
| Existing genuinely checked quadratic-reciprocity bodies reused | `174` |
| Other already-checked parent bodies independently rebuilt | `15` |
| Actual original proof bodies independently reconstructed | `216` |
| Ordered 390-row theorem-name SHA-256 | `9a94742066b28f553ad78fd675c41354a461cbe5f69f8e5df3ec36f9b055a843` |
| Ordered 201-row body-only name SHA-256 | `f1b2a83e8f7ec612a9a1dd564902fc543dc5833907b3c8a355f2c22a96a85c71` |
| Exact immutable graph/surface SHA-256 | `1ed816a1f32ec90601d58d46eb4e7bec27775a0b9c1d7b5fba84ac377231de9f` |

**Release distinction:** this complete research proof does not rewrite Alpha
v17, grant checked-use authority, admit the theorem to Stable, or create a
successor edition. `four_square_lagrange` truthfully remains `body_checked` in
immutable Alpha v17. A separately reviewed dependency-closed release promotion
would be required before its proof could cross that checked-use boundary.

The five older body-only prerequisites are:

```text
mul_le_mul
mul_shuffle_four
two_mul_eq_add_self
square_lt_successor_square
mul_le_cancel_left_nonzero
```

The exact 201-row missing-proof frontier has fifteen dependency-ready waves:

```text
63 → 37 → 21 → 19 → 12 → 9 → 5 → 4 → 12 → 11 → 3 → 2 → 1 → 1 → 1
```

These counts only describe scheduling. The actual stored proof trees, not wave
labels or source metadata, are what both independent checkers verify.

## Durable complete unconditional proof artifact

```text
research/arithmetic-library/artifacts/four-square-proof-bundle-v1.json
```

Exact canonical identity and measured proof resources:

```text
format:                peano-lab-bundle-v1
bytes:                 1948314
SHA256:                dd8374b95184f95f28a296aba6682f8177538650c3cc2f8d94a8db723c9982f0
theorem/root nodes:    390
root local ID:         389
dependency edges:      1187
body-proof occurrences:31942
original-kernel calls: 390
peak resident memory:  560.5 MiB
hard resident guard:   1536 MiB
```

The final root is the exact original unconditional Lagrange statement, not an
auxiliary conjunction or a conditional descent theorem. Its original immediate
premises are:

```text
four_square_prime_representation
four_square_lagrange_from_all_primes
```

Both are fully proved in the same 390-node graph, together with their complete
transitive prerequisites. Every bundle node contains its exact first-order
target, exact local dependency IDs, and its entire ordinary constructive
dependency-curried proof tree.

The 216 reconstructed proofs were checked in 14 bounded microbatches: thirteen
16-row batches and one 8-row batch. The largest actual batch used only 6,650
structural proof occurrences and 6,650 proof objects, safely below the
unchanged hard limits of 125,000 structural occurrences, 25,000 proof objects,
and 16 proof bodies per batch.

## Actual ordinary empty-context Lagrange proof

The complete canonical 390-node graph was also compiled, in a fresh process,
using the unchanged existing layered constructive `Cut` compiler. No new
proof constructor, external premise, trusted theorem reference, or modified
resource limit was introduced. The original independent kernel accepted:

```text
check(
  (),
  ordinary_complete_lagrange_certificate,
  _closed_formula(four_square_lagrange.statement),
) = True
```

Exact measured successful ordinary-proof resources:

| Metric | Actual measured value | Existing hard boundary |
|---|---:|---:|
| Structural ordinary proof occurrences | `40,466` | unchanged layered compiler bound `500,000` |
| Fresh-process peak resident memory | `577.4` MiB | independently monitored `1,536` MiB |
| Complete load, graph check, compile, and kernel check | `33.7` seconds | original unchanged resource policy |
| Exact theorem dependency nodes | `390` | unchanged graph bound `4,096` |

The dedicated process monitored its resident memory every 250 milliseconds
and would have terminated immediately above the 1,536-MiB guard. Its actual
completion event was:

```json
{
  "event": "four_square_ordinary_root_kernel_checked",
  "name": "four_square_lagrange",
  "proof_nodes": 40466,
  "peak_rss_mib": 577.4,
  "elapsed_seconds": 33.7
}
```

Therefore this is not merely a dependency-curried body or a conditional
interpretation of the modular graph: it is an actual ordinary constructive
proof of the exact universal theorem from the empty context, accepted by the
unchanged existing kernel.

## Reproducing the independent checks

Check the canonical bytes from the repository root:

```console
shasum -a 256 \
  research/arithmetic-library/artifacts/four-square-proof-bundle-v1.json
```

Expected:

```text
dd8374b95184f95f28a296aba6682f8177538650c3cc2f8d94a8db723c9982f0
```

Independently check every actual theorem body using the separately compiled
Lean proof-bundle verifier:

```console
../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
  research/arithmetic-library/artifacts/four-square-proof-bundle-v1.json
```

Actual result:

```text
ACCEPT  .../four-square-proof-bundle-v1.json  nodes=390  root=389
```

Run the original-kernel, frozen-parent, exact-root, false-proof, changed-edge,
resource-policy, and immutable-release regression tests:

```console
cd peano-lab/py
python3 -m pytest -q tests/test_four_square_complete_closure.py
```

Rebuild every actual missing body under the existing 1,536-MiB memory guard
and independently recheck the full root graph:

```console
cd peano-lab/py
python3 -m peano_lab.library.four_square_complete_closure \
  --progress --max-rss-mib 1536 \
  --export /private/tmp/four-square-proof-bundle-v1.json
```

The exporter refuses to overwrite an existing destination. Missing actual
bodies, false theorem proofs, altered Alpha-v17 source rows, changed graph
edges, an incorrect root, mutated proof bytes, any out-of-policy microbatch,
or a changed canonical artifact SHA-256 all fail closed.
