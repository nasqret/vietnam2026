# Independently checked quadratic-reciprocity closure receipt

Date: **2026-08-25**.

The exact sign-free, two-case strict-Heyting-arithmetic theorem
`quadratic_reciprocity_combined` has now been proved from the empty context in
two independently checked representations:

1. One ordinary, self-contained layered `Cut` certificate was accepted by the
   **unchanged existing intuitionistic Python kernel** against the exact frozen
   quadratic-reciprocity formula.
2. A complete, self-contained 557-node dependency bundle was accepted by the
   unchanged Python kernel once per genuine theorem body and separately
   accepted by the compiled **independent Lean bundle verifier** against the
   same exact uncurried root formula.

No classical `DNE`, extra mathematical axiom, external theorem-name lookup,
trusted digest, host-arithmetic oracle, or `sorry` supplies proof authority.

## Exact source and immutable release boundary

| Property | Independently checked value |
|---|---|
| Root theorem | `quadratic_reciprocity_combined` |
| Root local ID | `556` |
| Theorem/dependency nodes | `557` |
| Direct dependency edges | `1,787` |
| Dependency layers | `45` |
| Stable-closed source rows | `241` |
| Alpha-closed source rows | `1` |
| Dependency-curried `body_checked` source rows | `314` |
| `pending_layered_closure` source rows | `1`, the root |
| Exact surface SHA-256 | `2a95f83a5a21a5e21e482d5de8a19d55ee1843f676f086438f8a9853b6a97070` |
| Exact dependency-graph SHA-256 | `26017364ea943c4ed51a4a83f63ff0cd56b0de3686f0e0b458e7548ee84b1253` |
| Exact candidate-source SHA-256 | `23fd18aaff26e2c6b428949c35ab3658252c9a4c6fd3b4825a6ccd547f454db1` |
| Frozen Alpha-v15 enrollment SHA-256 | `44be61cdff1a093a78684a9d001d61d2b3761e73bacf6e79fe1a456f4ce50175` |
| Frozen Alpha-v15 identity SHA-256 | `2f1a097ac0b6821c74cd4da088c396d3b9960ffd43e169f22b4778d5871adc66` |
| Promoted Alpha-v16 identity SHA-256 | `3a683daf384e1712222012e4a4929732a9ec73c87fb5acb8a69446e2bcad5f10` |
| Exact Alpha-v16 evidence-only promotions | `315`, including the final root |

The already sealed Alpha-v15 release has **not** been rewritten: its historical
immutable source partition above and root row remain
`pending_layered_closure`. A separately reviewed immutable Alpha-v16 successor
now promotes exactly the 314 formerly `body_checked` QR ancestors and their
formerly pending root to `alpha_closed`. Current Alpha checked-use authority
therefore rises from `570` to `885`; all `788` unrelated body-only entries
remain unavailable, and the official 432-theorem Stable/public registry is
unchanged. Hashes document provenance only: every newly promoted theorem use
decodes and checks the actual proof artifact through the original kernel.

## Ordinary unchanged-kernel empty-context certificate

The complete ordinary certificate uses only the proof constructors already
accepted by `peano_lab.kernel.checker.check`. The final actual judgment was:

```text
check((), certificate, _closed_formula(QUADRATIC_RECIPROCITY_COMBINED))
  = True
```

Measured exact full-certificate resources:

| Metric | Actual | Unchanged admission bound |
|---|---:|---:|
| Structural proof occurrences | `54,870` | `500,000` |
| Distinct proof objects | `35,052` | `100,000` |
| Proof depth | `129` | `256` |
| Formula/term annotation occurrences | `252,961` | `5,000,000` |
| Actual body count | `557` | graph bound `4,096` |
| Balanced dependency-package layers | `45` | proof-depth bound `256` |
| Peak resident memory | `843,087,872` bytes, approximately `804` MiB | explicit `1,536` MiB campaign guard |
| Complete checkpoint/build/bundle/root run | `602.9774` seconds | resource-bounded workstation run |

This is a genuine accepted ordinary empty-context proof, not a conditional
body-only replay, an accepting dummy-target scaffold, or an inferred closure
from Lean alone. Its proof object was checked during the measured run; the
durable artifact below stores the smaller complete modular proof data from
which the same ordinary certificate can be rebuilt.

## Durable complete proof artifact

Repository artifact:

```text
research/arithmetic-library/artifacts/quadratic-reciprocity-proof-bundle-v1.json
```

Exact artifact identity:

```text
format: peano-lab-bundle-v1
bytes:  2790229
SHA256: 3cd040d145f1004d07d277c66a3ffbcb355cd9c4b21938d79a6ec51b4258709c
```

The artifact contains every target, every dependency edge, every complete
ordinary dependency-curried proof tree, and the exact root. Its graph has
`41,722` structural body-proof occurrences, and checking it invokes the
unchanged intuitionistic Python kernel exactly `557` times. Neither the SHA-256
nor a stored receipt is accepted as theorem evidence: the actual proof bytes
are decoded and each body is checked independently.

The construction used `35` canonical bounded checkpoints, each containing at
most `16` genuine proof bodies. The largest actual microbatch contained only
`2,398` proof occurrences and `2,398` independently rehydrated proof objects,
well below the fixed `125,000`-occurrence and `25,000`-object workstation
policies. Canonical self-contained serialization correctly charges proof trees
without assuming Python object-identity sharing survives checkpoint reload.

## Reproducing the independent checks

From the repository root, verify the exact bytes:

```console
shasum -a 256 \
  research/arithmetic-library/artifacts/quadratic-reciprocity-proof-bundle-v1.json
```

Expected:

```text
3cd040d145f1004d07d277c66a3ffbcb355cd9c4b21938d79a6ec51b4258709c
```

Run the focused fail-closed suite, including a fresh real-kernel check of all
557 artifact bodies, exact SHA and topology, false-proof mutations, classical
proof rejection, checkpoint provenance, resource bounds, and the distinction
between a dependency-curried body and a closed theorem:

```console
cd peano-lab/py
python3 -m pytest -q tests/test_quadratic_reciprocity_bounded_closure.py
```

The recorded result was:

```text
21 passed in 8.70s
```

The broader joint regression also included the existing quadratic-reciprocity
stack and user-owned experiment test, generic layered replay, the complete
proof-bundle codec, and the grand-campaign dependency graph:

```text
126 passed in 17.06s
```

From the main repository root, independently check the same uncurried root with
the separately compiled Lean executable:

```console
../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
  research/arithmetic-library/artifacts/quadratic-reciprocity-proof-bundle-v1.json
```

Actual output:

```text
ACCEPT  .../quadratic-reciprocity-proof-bundle-v1.json  nodes=557  root=556
```

To rebuild all actual bodies in safe dependency-ready batches, persist their
complete bounded proof bytes, recheck the full modular graph, and finally ask
the original kernel to check the single ordinary empty-context certificate:

```console
cd peano-lab/py
python3 -m peano_lab.library.quadratic_reciprocity_closure \
  --checkpoint-dir /private/tmp/peano-qr-replay \
  --all --assemble --max-rss-mib 1536
```

The required final event is:

```json
{
  "event": "ordinary_qr_root_kernel_checked",
  "body_count": 557,
  "edges": 1787,
  "layers": 45,
  "proof_nodes": 54870,
  "proof_objects": 35052,
  "proof_depth": 129,
  "annotation_occurrences": 252961
}
```

Timings and peak resident memory vary with the host. Missing proof bodies,
false roots, changed targets or dependency edges, noncanonical proof bytes,
`DNE`, altered source/Alpha identities, unsafe microbatch sizes, and violations
of the unchanged proof-envelope limits must all fail closed.
