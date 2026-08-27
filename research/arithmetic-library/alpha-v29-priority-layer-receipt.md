# Alpha v29 priority-layer complete proof receipt

Date: 2026-08-27. This receipt records observed proof checks. It is not an
axiom, an inference rule or a replacement for the ordinary proof data.

## Exact canonical artifact

```text
research/arithmetic-library/artifacts/alpha-v29-priority-layer-proof-bundle-v1.json

new theorem bodies:            278
inherited theorem bodies:      287
actual theorem bodies:         565
maximal endpoints:              29
conjunction packaging nodes:     1  (not a library theorem)
total bundle nodes:            566
ordinary dependency edges:    1661
total bundle edges:           1690
structural body occurrences: 38443
original kernel calls:         566
root node:                     565
artifact bytes:            4200971
artifact SHA-256:
4fcb3cd45e83448776abb9e33692496a7acfa98a051cae15761826a0b15fda44
actual-cone ordered-name SHA-256:
ce8ccc0cbbd5cac4fd5b24187c4c865f43c2a5080fd1cfdc2234ececb26bb47b
```

The exact parent is the unmodified 2,764-theorem Alpha v28 catalogue with
SHA-256 `897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9`.
The additive edition contains 3,042 checked-use entries, 9,915 theorem
edges and 53 layers. Stable remains the object-identical default 432.

```text
v29 edition identity:
57da70c3718579cb8eb81c59a4c2898a5071140fa944e31bca312fe53432574c
v29 ordered enrollment:
feac02afbfe516116accd30a6a117060f5d5cd99d608971a7f62bd1f3787104d
```

## Frozen mathematical work

| Campaign | Rows | Edges | Ordinary commands | Body occurrences | Largest body | Maximum depth |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Shared prime valuation support | 20 | 81 | 1,122 | 1,767 | 358 | 73 |
| G072 continued-fraction approximation | 83 | 247 | 4,003 | 9,468 | 591 | 96 |
| G006 Euler totient product | 84 | 266 | 3,206 | 5,503 | 239 | 73 |
| G010 squarefree kernels and perfect-power profiles | 53 | 148 | 2,020 | 3,691 | 369 | 60 |
| G036 odd-prime lifting of the exponent | 38 | 189 | 2,157 | 4,096 | 583 | 63 |
| Total | 278 | 931 | 12,508 | 24,525 | 591 | 96 |

The mathematical suites passed 2,558 focused tests: 618 for shared support
and G010, 660 for G072, 1,084 for G006, and 196 for G036. They include all
278 actual dependency-curried bodies, exact public AST and guard checks,
constructive witness boundaries, conservative binder hygiene, and negative
proof mutations. No tests were skipped or weakened to obtain these results.
These candidate-body tests are additional evidence; the complete dependency
closure below is the stronger integration gate.

## Separate candidate checkpoints and final combination

The branches were first closed independently without enrollment. Each
reported node count includes its one conjunction packaging node.

| Checkpoint | Bundle nodes | Edges | Body occurrences | Bytes | Builder seconds | Peak resident bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| G010, including shared support | 286 | 749 | 15,492 | 1,652,169 | not recorded | 841,170,944 |
| G036, including shared support | 264 | 774 | 15,576 | 1,336,410 | 106.676 | 761,675,776 |
| G006, including shared support | 352 | 992 | 19,448 | 2,086,863 | 99.011 | 912,179,200 |
| G072 | 217 | 557 | 15,298 | 1,160,452 | 99.953 | 735,150,080 |
| Combined first four, candidate export | 566 | 1,690 | 38,443 | 4,200,971 | 23.861 | 394,575,872 |
| Canonical v29 export, freshly checked | 566 | 1,690 | 38,443 | 4,200,971 | 23.921 | 306,642,944 |

The original branch payload digests are retained as reproducible diagnostics:

```text
G010: c4d239b9d699fb0dda942e6a2c2015333def7cde45497a7effe8e1cf2ccd785f
G036: 5046b29281227227bfd011c60fa8f1a0451ae6e57ab523c00511ea862fa420ff
G006: 1a39b9b9d94fd0bb1d8f91f769dc4fd971f11d31bf090d06b962c5c81b161e23
G072: 2e3e28bcd78d8b5a10fd35c7d8364603c1baef29e7869d594370c045ef3e7ccc
```

Only the canonical combined artifact is needed by the release. Permanent
tests reconstruct each branch from its exact named dependency cone in that
artifact, check the projected ordinary bodies again, and compare the exact
original encoded payload. No separate candidate file is runtime authority.

Every explicit seed was fully kernel-checked before exact target and ordered
prerequisite matching. The combined result was checked again. The canonical
export was not a file copy: the checked exporter read and checked the whole
combined seed, rebuilt the exact graph and packaging root, checked the result,
and wrote a new file using exclusive creation. It retained all 565 exact
theorem bodies. All 18 immutable historical proof-provider byte pins were
also checked, including providers unnecessary for the final combination.

Each reconstruction process used one-row batches, CPU soft/hard bounds of
170/175 seconds and a 180-second wall alarm. No existing body, term, formula,
sharing, kernel or bundle limit was raised. Peak measurements above are
observed local process measurements, not promised browser memory bounds.

To reproduce the canonical construction without retaining the temporary
candidate files, provide the existing canonical artifact as explicit proof
data and choose a destination that does not yet exist:

```sh
PYTHONPATH=peano-lab/py PYTHONMALLOC=malloc python3 \
  -m peano_lab.library.campaign_priority_layer_closure \
  /private/tmp/v29-priority-rebuilt-proof-bundle.json --batch-size 1 \
  --seed-bundle research/arithmetic-library/artifacts/alpha-v29-priority-layer-proof-bundle-v1.json
```

The seed is freshly checked, the exact dependency graph and conjunction
root are reconstructed, and the output is checked again before exclusive
file creation. Exporting proof data does not itself enroll a theorem.

## Independent compiled Lean checks

The following command accepted the canonical payload:

```sh
../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
  research/arithmetic-library/artifacts/alpha-v29-priority-layer-proof-bundle-v1.json
```

```text
ACCEPT research/arithmetic-library/artifacts/alpha-v29-priority-layer-proof-bundle-v1.json nodes=566 root=565
```

The observed canonical check took 0.344 seconds and peaked at 145,489,920
resident bytes. All four standalone candidates also passed this verifier:
G010 in 0.287 seconds, G036 in 0.288 seconds, G006 in 0.342 seconds and G072
in 0.237 seconds. The combined candidate check took 0.404 seconds.

The executable was an existing **Lean 4.28.0** build, not a newly compiled
4.31.0 binary. Its exact provenance is:

```text
binary: ../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify
binary bytes: 106787344
binary SHA-256:
22a49645acdee1a90bdf09861729d62b7a9c5bc20bc1f799ad05adc54ee0b033
binary build-trace SHA-256:
46e0668fc6da76c84106f7f95caf2aea5b3eaece14a97d6528327298703de4d5
PeanoLab/VerifyBundle build-trace SHA-256:
9c8c380802aba0f7405a62c6832751303438f51a16d1e2e2bb0f6098eb0465d3
compiler version, confirmed by the installed explicit toolchain executable:
Lean 4.28.0, arm64-apple-darwin24.6.0, Release
compiler commit: 7e01a1bf5c70fc6167d49c345d3bf80596e9a79b
```

The companion checkout's `lean-toolchain` requested `leanprover/lean4:v4.31.0`
at this observation, but that version was unavailable locally. No install or
private repository modification was attempted. A separate remote CI build
of the pinned 4.31.0 checker does not imply that this local artifact was
checked by 4.31.0. The receipt deliberately distinguishes those facts.

## Actual single-theorem empty-context checks

After complete bundle checking, the exact cone for each selected endpoint
was conservatively interned. Every interned body was checked again, the
ordinary certificate was materialized under the original limits, and
`check((), certificate, exact_formula)` succeeded. Proof-node counts below
refer to those full certificates, not to the candidate bodies.

| Endpoint | Ordinary proof nodes | Seconds | Peak resident bytes |
| --- | ---: | ---: | ---: |
| `positive_squarefree_kernel_and_power_profile` | 19,750 | 38.520 | 366,034,944 |
| `odd_prime_lifting_the_exponent` | 17,217 | 16.929 | 358,776,832 |
| `totient_euler_product_formula` | 24,921 | 62.333 | 398,934,016 |
| `continued_fraction_convergent_best_approximation` | 10,186 | 7.781 | 322,273,280 |
| `continued_fraction_convergent_best_approximation_signed` | 10,092 | 15.800 | 484,081,664 |

The first four measurements used the independently closed branch artifact;
the signed continued-fraction measurement used the canonical combined
artifact. They are ordinary original-kernel proofs, not trusted rule tags,
metadata lookups or a proof-by-hash. Certificates were discarded between
processes to avoid retaining unrelated proof objects.

The exact v29 metadata import also succeeded with 3,042 checked entries and
the identities above. Channel, publisher, global definition-DAG, browser,
deployment and Stable-promotion checks remain separate release gates.

## Final frozen closure and admission regressions

The complete closure suite passed **92 tests** in 128.62 seconds, with
752,517,120 peak resident bytes. The final admission suite passed **96
tests** in 111.24 seconds, with 1,019,314,176 peak resident bytes. Both used
fresh processes with the same 170/175-second CPU bounds and 180-second
wall alarm. There were no skips and no resource-limit increases.

The closure suite checks all 566 canonical proof nodes, exact branch
projection back to the original standalone bytes, separate occurrence and
identity budgets, source pins, missing/forward/duplicate dependencies,
classical or implicit scripts, forged seed bodies, wrong ordered premise
targets, invalid unused seed nodes, malformed seed paths, and exclusive
non-overwriting export. A canonical-bundle G010 theorem materializes as
an actual 19,750-node ordinary empty-context proof.

The admission suite checks all 3,042 entries, the 2,764 object-identical
parent entries, Stable identity and exclusion of every new theorem, all
33 principal statement pins, all factory/specification/provenance seals,
and every source/test/RFC path. It reads the canonical artifact through
the actual v29 checked-use runtime and verifies every exact target and
ordered edge. The actual `editions_v29.replay` path also materializes and
checks the 17,217-node full odd-prime LTE certificate.

Missing and altered proof files fail closed. Rebinding a forged payload's
byte count and digest does not make it valid: separate body, target,
dependency-order and packaging mutations are rejected by the actual
graph/original-kernel checks. Browser-layout tests retain exact supplied
parent authentication without a repository catalogue. All 18 inherited
ordinary proof providers remain byte-exact. These are executable checks,
not additional trust assumptions.
