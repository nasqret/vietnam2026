# Alpha v28 lower-layer complete proof receipt

Date: 2026-08-27. The full self-contained artifact passed the unchanged
intuitionistic HA kernel and the independently compiled Lean bundle
verifier. This is a diagnostic receipt, not an axiom or a replacement for
the ordinary proof bodies.

## Exact checked artifact

Artifact:
`research/arithmetic-library/artifacts/alpha-v28-lower-layer-proof-bundle-v1.json`

```text
new theorem bodies:          204
historical theorem bodies:   657
actual theorem bodies:       861
maximal theorem endpoints:    36
conjunction packaging nodes:   1  (not a library theorem)
total bundle nodes:          862
actual dependency edges:    3054
total bundle edges:         3090
structural body nodes:    230464
original kernel calls:       862
root node:                   861
artifact bytes:         18977050
artifact SHA-256:
e56dda386bf60759d1bacda45417eacd7e6a67fd6e23799f002aac9964253ae1

actual-cone ordered-name SHA-256:
d9900807b562cb3f6b5e40b398b4cc26e4ad0714dc5e7cc00263ada62ee73a15

new-frontier ordered-name SHA-256:
7882fe1fbcd64ee23668f62dcc45aa4a946a562c7da2fd5dba3b30612bccc402
```

All 204 new entries are Alpha-only and checked-use. Together with the
unchanged parent, Alpha v28 has 2,764 checked-use entries, 8,984 direct
theorem edges, and 53 layers. Stable remains the separate default 432.

The following values were computed from the actual decoded proof bodies;
body-node counts are structural occurrences, not source-line counts.

| Campaign | Theorems | Edges | Tactic commands | Body nodes | Largest body | Maximum depth |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Foundations | 28 | 86 | 1,596 | 3,219 | 713 | 60 |
| Signed/Gaussian Euclidean division | 93 | 320 | 4,591 | 14,765 | 736 | 108 |
| Eisenstein Euclidean division | 65 | 308 | 5,414 | 15,606 | 1,242 | 108 |
| Prime enumeration | 18 | 74 | 802 | 1,446 | 193 | 57 |
| Total | 204 | 788 | 12,403 | 35,036 | 1,242 | 108 |

The public presentation places the infinitude wrapper in the prime family,
giving 27 foundation and 19 prime-family pages; the immutable admission
origin remains 28 foundations and 18 prime-enumeration entries.

## Reconstruction and independent verification

The exported artifact was constructed by
`export_lower_layer_proof_bundle(..., batch_size=1)`, the same entrypoint
used by this reproducible command:

```sh
PYTHONPATH=peano-lab/py PYTHONMALLOC=malloc python3 \
  -m peano_lab.library.campaign_lower_layer_closure \
  research/arithmetic-library/artifacts/alpha-v28-lower-layer-proof-bundle-v1.json \
  --batch-size 1

../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
  research/arithmetic-library/artifacts/alpha-v28-lower-layer-proof-bundle-v1.json
```

Observed original-kernel result:

```text
lower-layer original-kernel ACCEPT: nodes=862; edges=3090;
body-nodes=230464; bytes=18977050;
sha256=e56dda386bf60759d1bacda45417eacd7e6a67fd6e23799f002aac9964253ae1
```

Observed compiled Lean result (tab-separated fields):

```text
ACCEPT research/arithmetic-library/artifacts/alpha-v28-lower-layer-proof-bundle-v1.json nodes=862 root=861
```

A subsequent cold read through the actual
`editions_v28.checked_lower_layer_bundle()` also accepted all 862 nodes,
3,090 edges, 230,464 body occurrences, and 861 theorem positions. Runtime
metadata contains the exact 2,764 checked entries and the pinned identities:

```text
v28 edition:
4936d155e8d2a39409a4e83beb4ac5cb2481948d8b6eeecf1c7571161786646b
v28 enrollment:
75c80dffb8899dbf6f97a561322e630679d9df58416309e5c439746e96466fce
```

All 17 historical proof providers passed their exact byte pins, including
unused providers. Of the 657 inherited theorem bodies, 630 were retained
after exact target and ordered-premise matching; 27 were reconstructed
from their unchanged scripts. All 204 new bodies were reconstructed. Every
one of the 231 reconstruction batches contained one theorem. No existing
row, proof-node, proof-object, formula, depth, or replay budget was raised.

The native combined assembly took 369.35 seconds and peaked at 915,636,224
resident bytes. This is an observed local measurement, not a promised
browser memory bound.

## Additional runtime availability checks

Before final combination, the exact proposed v28 runtime path materialized
and checked ordinary closed proofs for these strongest frozen endpoints:

| Endpoint | Closed proof nodes |
| --- | ---: |
| Full factorization existence and unordered permutation uniqueness | 17,225 |
| Actual exhaustive first-prime list and double-exponential bound | 202,799 |
| Full canonical Gaussian Euclidean division | 18,513 |

These used the exact applicable dependency cones in the intermediate
self-contained artifacts, the unchanged interning limits, per-body kernel
rechecks, and final certificate checking. They are additional availability
checks; the complete final artifact and cold v28 checked-use check above
are the admission evidence. Principal runtime certificates are discarded
between checks to avoid accumulating large proof objects.

## Focused mathematical audits

All six frozen provider test suites passed: 75 foundation-wrapper tests,
320 unordered-permutation tests, 27 shared signed-division tests, 439
Gaussian tests, 394 Eisenstein tests, and 157 prime-enumeration tests.
That is 1,412 focused tests, including every actual candidate body,
statement/dependency pins, negative proof and premise mutations, and
capture-safe relation constructors.

The exact nine milestone targets are G001–G005, G021, G022, G081, and G084.
Their zero/empty cases, actual witness construction, signed/code interfaces,
and excluded stronger claims are recorded in
`alpha-v28-lower-layer-rfc-v1.md` and the six individual mathematical RFCs.
Gaussian/Eisenstein gcd algorithms, unique factorization, and complete
prime classification are not silently admitted.

All 605 inherited v27 evidence records remain unchanged. The parent
catalogue SHA-256 is
`481a9a378e54dc389422819587e8377a07b63a0d5d50286ffdfd28f0c4bdb2e6`.
The historical audit-source dispositions remain exactly those of v27.
No proof artifact, kernel, or new evidence file receives an exception.

Channel, definition-atlas, publication, and browser checks are separate
release gates. No commit, push, remote publication, or Stable promotion
is asserted by this mathematical receipt.
