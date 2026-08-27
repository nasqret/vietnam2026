# Alpha v27 second-wave complete proof receipt

Date: 2026-08-27.

The full self-contained second-wave artifact was accepted by the unchanged
original intuitionistic HA kernel and by the independently compiled Lean
bundle verifier. This receipt is a diagnostic record, not an additional axiom
or a substitute for the actual ordinary proof bodies.

## Exact checked artifact

Artifact:
`research/arithmetic-library/artifacts/alpha-v27-second-wave-proof-bundle-v1.json`

```text
new theorem bodies:          422
historical theorem bodies:   801
actual theorem bodies:      1223
maximal theorem endpoints:    43
conjunction packaging nodes:   1  (not enrolled as a theorem)
total bundle nodes:         1224
actual dependency edges:    3956
total bundle edges:         3999
structural body nodes:    103215
original kernel calls:      1224
root node:                  1223
artifact bytes:         14648599
artifact SHA-256:
c4711433c92b67d2ebeb30131669c60563c70e0464dafa851d417fb88fb21a6d

actual-cone ordered-name SHA-256:
233695b3c7d32d48e81e7888bfd34ed6e41678c75e11ed967826e9fab3bf9e60

new-frontier ordered-name SHA-256:
e925d4355f63aad9874fac92a3ec05362162793ec1fc2eea909ac1e1ede8f01b
```

The exact frontier counts are 182 matrix/rank/span/data, 40 Hensel,
24 generalized CRT, 19 multinomial Kummer, 55 Chebyshev, 30 Cornacchia,
and 72 finite-set/Cauchy–Davenport theorems. Their 1,345 direct dependency
edges are added to the unchanged v26 inventory, yielding Alpha v27 with
2,560 checked-use entries, 8,196 edges, and 53 layers. Stable remains 432.

The following metrics were also recomputed from the decoded accepted artifact
(body-node counts are structural occurrences, not source-line counts):

| Campaign | Theorems | Edges | Tactic commands | Body nodes | Largest body | Maximum depth |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Integer linear algebra | 182 | 415 | 9,921 | 18,408 | 707 | 137 |
| Hensel | 40 | 197 | 2,692 | 4,422 | 475 | 71 |
| Generalized CRT | 24 | 72 | 1,099 | 2,104 | 351 | 62 |
| Multinomial Kummer | 19 | 55 | 841 | 1,615 | 375 | 56 |
| Chebyshev | 55 | 239 | 2,621 | 4,755 | 297 | 64 |
| Cornacchia | 30 | 112 | 1,190 | 2,326 | 210 | 69 |
| Cauchy–Davenport | 72 | 255 | 4,626 | 7,230 | 384 | 78 |
| Total | 422 | 1,345 | 22,990 | 40,860 | 707 | 137 |

The seven primary milestone theorem nodes in the self-contained artifact are
896 (rank), 1022 (all-positive-power Hensel), 1041 (normalized finite CRT),
1063 (multinomial Kummer), 1114 (Chebyshev), 1150 (Cornacchia), and
1221 (Cauchy–Davenport). Their full statements are the original exact
catalogue statements; the final node 1223 is only the conjunction package.

## Actual verification commands

```sh
PYTHONPATH=peano-lab/py PYTHONMALLOC=malloc python3 \
  -m peano_lab.library.campaign_second_wave_closure \
  research/arithmetic-library/artifacts/alpha-v27-second-wave-proof-bundle-v1.json

../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
  research/arithmetic-library/artifacts/alpha-v27-second-wave-proof-bundle-v1.json
```

Observed original-kernel result:

```text
second-wave original-kernel ACCEPT: nodes=1224; edges=3999;
body-nodes=103215; bytes=14648599;
sha256=c4711433c92b67d2ebeb30131669c60563c70e0464dafa851d417fb88fb21a6d
```

Observed compiled Lean result (tab-separated fields):

```text
ACCEPT research/arithmetic-library/artifacts/alpha-v27-second-wave-proof-bundle-v1.json nodes=1224 root=1223
```

A separate cold read through `checked_second_wave_proof_bundle()` also
accepted the exact artifact and all metrics. The compiled checker validates
the self-contained HA proof encoding; this is not a claim that printed
prose or a JSON receipt alone is a Lean proof.

## Authority and reuse

Of the 801 actual inherited theorem bodies, 791 were retained from the
smallest matching frozen historical artifacts; ten were reconstructed from
their exact original scripts. All 422 new bodies were reconstructed. The
complete 432 reconstructed-body run used one-row microbatches, without
altering any existing row/node/object/depth budget. Every retained body
matched both its target and ordered dependency targets and was checked again
in the final graph.

The 43 maximal endpoint hypotheses are all genuinely used by the balanced
conjunction proof. There are no unused decorative dependency edges at the
packaging root, no classical DNE, no `sorry`/`admit`, and no new kernel rule.

The individual campaign RFCs and focused tests pin the exact endpoint
formulas, zero/empty cases, witness construction, negative mutations, body
metrics, and capture-safe public relation builders. The combined closure and
definition suite passed 1,099 tests after all 422 rows and 67 new definitions
were integrated, before adding the final sealed-artifact regression cases.
Publication, channel, browser, and application checks are separate release
gates and do not confer mathematical authority by themselves.

## Scope and historical evidence

The exact seven named second-wave targets are T13, G011, G095, G035, G027,
G051, and G107. Their representation refinements and unclaimed stronger
results are specified in `alpha-v27-second-wave-rfc-v1.md`. Broader roadmap
bullets are not silently marked complete.

The v26 catalogue SHA-256 remains
`969c261f924060552dda393427b4fbc51515b9d4e69daa17f5e9f1691b5ab534`.
The 535 inherited evidence records remain exact. The five historical
audit/source files already revised by earlier commits are explicitly
distinguished in the RFC and publisher manifest; this campaign did not edit
them or treat their later bytes as the older recorded versions. The actual
historical proof providers used in this closure all passed exact byte pins.

No commit, push, remote publication, or Stable promotion is part of this
receipt.
